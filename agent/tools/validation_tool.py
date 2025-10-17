from typing import Any, Dict, List, Optional, Tuple
import os
import json
import re

from agent.llm.hub import LLMHub
from agent.prompts.validation_prompts import SYSTEM_PROMPT, CRITIQUE_USER_TEMPLATE


class ValidationTool:
    def __init__(self, hub: Optional[LLMHub] = None, config: Optional[Dict[str, Any]] = None) -> None:
        self.hub = hub
        self.cfg = config or self._load_config()

        vcfg = self.cfg
        self.min_len: int = int(vcfg.get("min_len", 6))
        self.max_len: int = int(vcfg.get("max_len", 180))
        self.banned_words: List[str] = list(vcfg.get("banned_words", []))
        self.require_abcd_format: bool = bool(vcfg.get("require_abcd_format", True))
        self.unique_options: bool = bool(vcfg.get("unique_options", True))
        self.grade_numeric_range: Dict[str, List[int]] = vcfg.get("grade_numeric_range", {"grade1": [0, 100]})
        self.enable_math_check: bool = bool(vcfg.get("enable_math_check", True))
        self.enable_llm_critique: bool = bool(vcfg.get("enable_llm_critique", False))
        self.auto_fix_once: bool = bool(vcfg.get("auto_fix_once", True))

    def _load_config(self) -> Dict[str, Any]:
        path = os.path.join(os.getcwd(), "configs", "agent.yaml")
        try:
            import yaml  # type: ignore
            if os.path.isfile(path):
                with open(path, "r", encoding="utf-8") as f:
                    data = yaml.safe_load(f) or {}
                    return data.get("validation", {}) or {}
        except Exception:
            return {}
        return {}

    def validate(
        self,
        questions: List[Dict[str, Any]],
        *,
        skill: Optional[str] = None,
        teacher_context: Optional[List[Dict[str, Any]]] = None,
        textbook_context: Optional[List[Dict[str, Any]]] = None,
        grade: Optional[int] = 1,
    ) -> Dict[str, Any]:
        teacher_context = teacher_context or []
        textbook_context = textbook_context or []

        all_issues: List[Dict[str, str]] = []
        debug_flags: Dict[str, Any] = {
            "enable_llm_critique": self.enable_llm_critique,
            "hub_attached": self.hub is not None,
            "critique_branch_executed": False,
        }

        # 1) Rule-based
        for q in questions:
            all_issues.extend(self._rule_checks(q))

        # 2) Math checks
        if self.enable_math_check:
            for q in questions:
                all_issues.extend(self._math_checks(q, grade=grade))

        # 3) LLM critique (optional, best-effort)
        suggested_fixes: List[Dict[str, Any]] = []
        if self.enable_llm_critique and self.hub is not None:
            debug_flags["critique_branch_executed"] = True
            critique = self._llm_critique(questions, teacher_context, textbook_context)
            all_issues.extend(critique.get("issues", []))
            suggested_fixes.extend(critique.get("suggested_fixes", []))

        # 4) Auto-fix once (lightweight)
        applied_fixes: List[Dict[str, Any]] = []
        if self.auto_fix_once:
            questions, applied_fixes = self._auto_fix(questions, all_issues)

        status = "approved" if not all_issues else "revise"
        confidence = self._score_confidence(all_issues, applied_fixes)

        return {
            "status": status,
            "issues": all_issues,
            "suggested_fixes": suggested_fixes,
            "applied_fixes": applied_fixes,
            "confidence": confidence,
            "validated_questions": questions,
            "debug_flags": debug_flags,
        }

    # --------------------- helpers ---------------------
    def _rule_checks(self, q: Dict[str, Any]) -> List[Dict[str, str]]:
        issues: List[Dict[str, str]] = []
        allowed_types = {"multiple_choice", "true_false", "fill_blank"}
        qid = q.get("question_id", "?")
        qtype = q.get("question_type")
        text = (q.get("question_text") or "").strip()

        if qtype not in allowed_types:
            issues.append({"code": "INVALID_TYPE", "message": f"question {qid}: unsupported question_type '{qtype}'"})
            return issues

        if len(text) < self.min_len or len(text) > self.max_len:
            issues.append({"code": "LEN_RANGE", "message": f"question {qid}: length out of range"})

        lowered = text.lower()
        for w in self.banned_words:
            if w and w.lower() in lowered:
                issues.append({"code": "BANNED_WORD", "message": f"question {qid}: contains banned word '{w}'"})

        answers = q.get("answers", [])
        if not isinstance(answers, list):
            issues.append({"code": "ANS_NOT_LIST", "message": f"question {qid}: answers must be a list"})
            return issues

        # per-type count
        if qtype == "true_false":
            if len(answers) != 2:
                issues.append({"code": "TF_ANS_COUNT", "message": f"question {qid}: TRUE_FALSE must have exactly 2 answers"})
        else:
            if len(answers) != 4:
                issues.append({"code": "CHOICE_ANS_COUNT", "message": f"question {qid}: {qtype} must have exactly 4 answers"})

        # exactly one correct
        correct_count = sum(1 for a in answers if isinstance(a, dict) and a.get("correct") is True)
        if correct_count != 1:
            issues.append({"code": "CORRECT_COUNT", "message": f"question {qid}: must have exactly 1 correct answer"})

        # unique options
        if self.unique_options:
            normalized = [str(a.get("text", "")).strip().lower() for a in answers if isinstance(a, dict)]
            if len(set(normalized)) != len(normalized):
                issues.append({"code": "DUP_OPTION", "message": f"question {qid}: duplicated answer options"})

        # ABCD formatting (optional)
        if self.require_abcd_format and qtype in {"multiple_choice", "fill_blank"} and isinstance(answers, list) and len(answers) == 4:
            # Require distinct and non-empty
            for idx, a in enumerate(answers):
                if not isinstance(a, dict) or not str(a.get("text", "")).strip():
                    issues.append({"code": "EMPTY_OPTION", "message": f"question {qid}: empty option at {idx}"})

        # banned words in answers
        for a in answers:
            if not isinstance(a, dict):
                continue
            at = str(a.get("text", ""))
            low = at.lower()
            for w in self.banned_words:
                if w and w.lower() in low:
                    issues.append({"code": "BANNED_WORD", "message": f"question {qid}: answer contains banned word '{w}'"})

        return issues

    def _math_checks(self, q: Dict[str, Any], *, grade: Optional[int] = 1) -> List[Dict[str, str]]:
        issues: List[Dict[str, str]] = []
        qid = q.get("question_id", "?")
        text = (q.get("question_text") or "").lower()

        # Detect simple expressions: a + b, a - b
        m = re.search(r"(\d+)\s*([+\-])\s*(\d+)", text)
        if not m:
            return issues

        a, op, b = int(m.group(1)), m.group(2), int(m.group(3))
        correct = a + b if op == "+" else a - b

        # Range by grade
        lo, hi = self.grade_numeric_range.get(f"grade{grade}", [None, None])
        if lo is not None and (a < lo or b < lo or correct < lo):
            issues.append({"code": "OUT_OF_RANGE", "message": f"question {qid}: values below range"})
        if hi is not None and (a > hi or b > hi or correct > hi):
            issues.append({"code": "OUT_OF_RANGE", "message": f"question {qid}: values above range"})

        # Validate answers contain exactly one correct numeric value
        answers = q.get("answers", [])
        nums = []
        correct_flags = 0
        for ans in answers:
            if not isinstance(ans, dict):
                continue
            try:
                # extract first integer in option
                nm = re.search(r"-?\d+", str(ans.get("text", "")))
                val = int(nm.group(0)) if nm else None
            except Exception:
                val = None
            nums.append(val)
            if ans.get("correct") is True:
                correct_flags += 1

        if correct_flags != 1:
            issues.append({"code": "CORRECT_COUNT", "message": f"question {qid}: must have exactly 1 correct answer"})
        if correct not in (n for n in nums if n is not None):
            issues.append({"code": "MATH_INCORRECT", "message": f"question {qid}: correct result {correct} not present in options"})

        return issues

    def _llm_critique(
        self,
        questions: List[Dict[str, Any]],
        teacher_context: List[Dict[str, Any]],
        textbook_context: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        def _extract_json_payload(text: str) -> Dict[str, Any]:
            try:
                return json.loads(text)
            except Exception:
                pass
            # try extract largest JSON object
            try:
                m = re.findall(r"\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}", text, flags=re.DOTALL)
                if m:
                    # choose the longest candidate
                    candidate = max(m, key=len)
                    return json.loads(candidate)
            except Exception:
                pass
            # try markdown code block ```json ... ``` or ``` ... ```
            try:
                m = re.search(r"```json\s*\n(.*?)\n```", text, flags=re.DOTALL | re.IGNORECASE)
                if m:
                    return json.loads(m.group(1))
                m = re.search(r"```\s*\n(.*?)\n```", text, flags=re.DOTALL)
                if m:
                    block = m.group(1).strip()
                    if block.startswith("{") and block.endswith("}"):
                        return json.loads(block)
            except Exception:
                pass
            return {}

        try:
            messages = [
                {"role": "system", "content": SYSTEM_PROMPT},
                {
                    "role": "user",
                    "content": CRITIQUE_USER_TEMPLATE.format(
                        questions=json.dumps(questions, ensure_ascii=False),
                        teacher_context=json.dumps(teacher_context, ensure_ascii=False),
                        textbook_context=json.dumps(textbook_context, ensure_ascii=False),
                    ),
                },
            ]
            try:
                output, _ = self.hub.call(messages=messages, temperature=0.1, max_tokens=512)
            except Exception as e:
                return {
                    "issues": [{
                        "question_id": "*",
                        "code": "LLM_CRITIQUE_CALL_ERROR",
                        "message": f"Hub call failed: {type(e).__name__}: {e}"
                    }],
                    "suggested_fixes": [],
                }

            data = _extract_json_payload(output)
            if not isinstance(data, dict) or ("issues" not in data and "suggested_fixes" not in data):
                return {
                    "issues": [{
                        "question_id": "*",
                        "code": "LLM_CRITIQUE_FORMAT",
                        "message": "Critique output not in expected JSON format"
                    }],
                    "suggested_fixes": [],
                }

            issues = data.get("issues", []) if isinstance(data, dict) else []
            suggested = data.get("suggested_fixes", []) if isinstance(data, dict) else []
            # sanitize (chỉ yêu cầu có 'code'; message có thể thiếu)
            issues = [i for i in issues if isinstance(i, dict) and i.get("code") is not None]
            suggested = [s for s in suggested if isinstance(s, dict) and s.get("question_id")]
            return {"issues": issues, "suggested_fixes": suggested}
        except Exception as e:
            return {
                "issues": [{
                    "question_id": "*",
                    "code": "LLM_CRITIQUE_ERROR",
                    "message": f"Unhandled critique error: {type(e).__name__}: {e}"
                }],
                "suggested_fixes": [],
            }

    def _auto_fix(self, questions: List[Dict[str, Any]], issues: List[Dict[str, str]]) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
        applied: List[Dict[str, Any]] = []
        # simple dedupe options and ensure one-correct
        for q in questions:
            qid = q.get("question_id", "?")
            answers = q.get("answers", [])
            # dedupe texts
            seen = set()
            for a in answers:
                if not isinstance(a, dict):
                    continue
                t = str(a.get("text", "")).strip()
                key = t.lower()
                if key in seen or not t:
                    a["text"] = f"Phương án {len(seen)+1}"
                seen.add(a["text"].lower())

            # ensure exactly one correct: keep first True, flip others
            found = False
            for a in answers:
                if isinstance(a, dict) and a.get("correct") is True:
                    if not found:
                        found = True
                    else:
                        a["correct"] = False
            if not found and isinstance(answers, list) and answers:
                answers[0]["correct"] = True
                for a in answers[1:]:
                    if isinstance(a, dict):
                        a["correct"] = False

            applied.append({"question_id": qid, "fix": "dedupe+one-correct"})
        return questions, applied

    def _score_confidence(self, issues: List[Dict[str, str]], applied_fixes: List[Dict[str, Any]]) -> float:
        if not issues:
            return 0.95
        score = 0.9
        # heavier penalties for structural issues
        penalties = {
            "INVALID_TYPE": 0.3,
            "ANS_COUNT": 0.25,
            "TF_ANS_COUNT": 0.25,
            "CHOICE_ANS_COUNT": 0.25,
            "CORRECT_COUNT": 0.25,
            "MATH_INCORRECT": 0.2,
            "OUT_OF_RANGE": 0.1,
            "DUP_OPTION": 0.1,
            "LEN_RANGE": 0.05,
            "BANNED_WORD": 0.05,
            "LLM_CRITIQUE": 0.05,
        }
        for i in issues:
            score -= penalties.get(i.get("code", ""), 0.02)
        if applied_fixes:
            score -= 0.05
        return max(0.1, min(0.95, score))


