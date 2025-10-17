from typing import Any, Dict, List, Tuple
import os
import time
import logging

from agent.tools import RAGTool, QuestionGenerationTool, ValidationTool
from agent.llm.hub import LLMHub


logger = logging.getLogger(__name__)


class AgentWorkflow:
    def __init__(self, hub: LLMHub | None = None, config: Dict[str, Any] | None = None) -> None:
        self.rag = RAGTool()
        self.hub = hub or LLMHub(providers=[])
        self.generator = QuestionGenerationTool(self.hub)
        self.validator = ValidationTool()
        self.cfg = config or self._load_config()
        self.regen_limit = int(self.cfg.get("regen_limit", 2))
        self.min_score = float(self.cfg.get("min_score", 0.0))
        self.max_teacher_ctx = int(self.cfg.get("max_teacher_ctx", 5))
        self.max_textbook_ctx = int(self.cfg.get("max_textbook_ctx", 20))

    def _load_config(self) -> Dict[str, Any]:
        try:
            import yaml  # type: ignore
            path = os.path.join(os.getcwd(), "configs", "agent.yaml")
            if os.path.isfile(path):
                with open(path, "r", encoding="utf-8") as f:
                    data = yaml.safe_load(f) or {}
                    return data.get("workflow", {}) or {}
        except Exception:
            return {}
        return {}

    def run(self, profile_student: Dict[str, Any], constraints: Dict[str, Any]) -> Dict[str, Any]:
        t0 = time.time()
        attempts = 0
        last_issues: List[Dict[str, Any]] = []

        # INIT → NORMALIZE_SKILL
        grade = constraints.get("grade", 1)
        skill = constraints.get("skill", "")
        skill_name = constraints.get("skill_name")
        num_questions = constraints.get("num_questions", 6)
        norm_skill_name = self._normalize_skill(skill_name)

        # RETRIEVE_SGV / RETRIEVE_SGK
        rag = self.rag.query(
            grade=grade,
            skill=skill,
            skill_name=norm_skill_name,
            topk_sgv=self.max_teacher_ctx,
            topk_sgk=self.max_textbook_ctx,
        )

        # MERGE_RERANK: (đã rerank trong RAGTool) — chỉ lọc theo min_score
        teacher_ctx = [x for x in rag.get("teacher_context", []) if float(x.get("score", 0.0)) >= self.min_score][: self.max_teacher_ctx]
        textbook_ctx = [x for x in rag.get("textbook_context", []) if float(x.get("score", 0.0)) >= self.min_score][: self.max_textbook_ctx]

        # GENERATE → VALIDATE loop
        all_questions: List[Dict[str, Any]] = []
        metadata: Dict[str, Any] = {"attempts": 0, "timings": {}, "validation": {}, "provider_used": "llm_hub"}
        while attempts <= self.regen_limit:
            attempts += 1
            metadata["attempts"] = attempts

            g0 = time.time()
            gen = self.generator.generate(
                teacher_context=teacher_ctx,
                textbook_context=textbook_ctx,
                profile_student=profile_student,
                constraints={
                    **constraints,
                    "skill_name": norm_skill_name or skill_name or "",
                },
            )
            metadata["timings"][f"gen_attempt_{attempts}"] = int((time.time() - g0) * 1000)
            questions = gen.get("questions", [])
            all_questions = questions

            v0 = time.time()
            report = self.validator.validate(questions, skill=skill, teacher_context=teacher_ctx, textbook_context=textbook_ctx, grade=grade)
            metadata["timings"][f"val_attempt_{attempts}"] = int((time.time() - v0) * 1000)
            metadata["validation"] = {"status": report.get("status"), "issues": report.get("issues", [])}
            last_issues = report.get("issues", [])

            if report.get("status") == "approved":
                break

            # nếu revise và chưa vượt regen_limit: điều chỉnh nhẹ nhiệt độ/batch nếu cần (đã có retry bên trong generator)
            logger.info("Validation revise; retry generation (attempt %s/%s)", attempts, self.regen_limit)

            if attempts > self.regen_limit:
                break

        total_ms = int((time.time() - t0) * 1000)

        return {
            "questions": all_questions,
            "teacher_context_ids": [x.get("id", "") for x in teacher_ctx],
            "textbook_context_ids": [x.get("id", "") for x in textbook_ctx],
            "metadata": {
                **metadata,
                "latency_ms": total_ms,
                "num_questions": len(all_questions),
                "regen_attempts": attempts - 1,
                "validation_issue_codes": [i.get("code") for i in last_issues if isinstance(i, dict)],
                "teacher_context_count": len(teacher_ctx),
                "textbook_context_count": len(textbook_ctx),
            },
        }

    # ----------------- helpers -----------------
    def _normalize_skill(self, skill_name: str | None) -> str | None:
        if not skill_name:
            return None
        try:
            from agent.tools.rag_tool import _normalize_lesson  # reuse logic
            return _normalize_lesson(skill_name)
        except Exception:
            return skill_name


