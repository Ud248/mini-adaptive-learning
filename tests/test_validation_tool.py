import json
import types

import pytest

from agent.tools.validation_tool import ValidationTool


def make_mcq(question_id: str = "q1"):
    return {
        "question_id": question_id,
        "question_text": "2 + 3 bằng mấy?",
        "question_type": "multiple_choice",
        "answers": [
            {"text": "5", "correct": True},
            {"text": "4", "correct": False},
            {"text": "6", "correct": False},
            {"text": "7", "correct": False},
        ],
    }


def make_tf(question_id: str = "q2"):
    return {
        "question_id": question_id,
        "question_text": "3 + 4 = 7 là đúng hay sai?",
        "question_type": "true_false",
        "answers": [
            {"text": "Đúng", "correct": True},
            {"text": "Sai", "correct": False},
        ],
    }


def test_multiple_choice_valid_passes():
    vt = ValidationTool(config={
        "enable_math_check": True,
        "enable_llm_critique": False,
        "auto_fix_once": False,
    })
    res = vt.validate([make_mcq()], grade=1)
    assert res["status"] == "approved"
    assert res["issues"] == []
    assert res["validated_questions"][0]["question_id"] == "q1"


def test_true_false_wrong_answer_count_flags_issue():
    vt = ValidationTool(config={"auto_fix_once": False})
    q = make_tf()
    q["answers"].append({"text": "Không rõ", "correct": False})
    res = vt.validate([q])
    assert res["status"] == "revise"
    codes = [i["code"] for i in res["issues"]]
    assert "TF_ANS_COUNT" in codes


def test_duplicate_options_autofix_and_one_correct():
    vt = ValidationTool(config={"auto_fix_once": True})
    q = make_mcq("q3")
    # duplicate option text and multiple correct flags
    q["answers"] = [
        {"text": "5", "correct": True},
        {"text": "5", "correct": True},
        {"text": "5", "correct": False},
        {"text": "", "correct": False},
    ]
    res = vt.validate([q])
    # Should still have issues reported, but auto-fix applied
    assert isinstance(res.get("applied_fixes"), list)
    fixed_q = res["validated_questions"][0]
    texts = [a.get("text") for a in fixed_q["answers"]]
    assert len(set(t.lower() for t in texts)) == 4  # deduped
    # ensure exactly one correct
    assert sum(1 for a in fixed_q["answers"] if a.get("correct") is True) == 1


def test_math_check_detects_missing_correct_option():
    vt = ValidationTool(config={
        "enable_math_check": True,
        "grade_numeric_range": {"grade1": [0, 100]},
        "auto_fix_once": False,
    })
    q = {
        "question_id": "q4",
        "question_text": "10 - 4 = ?",
        "question_type": "multiple_choice",
        "answers": [
            {"text": "3", "correct": False},
            {"text": "5", "correct": False},  # correct should be 6, but not present
            {"text": "7", "correct": True},
            {"text": "8", "correct": False},
        ],
    }
    res = vt.validate([q], grade=1)
    codes = [i["code"] for i in res["issues"]]
    assert "MATH_INCORRECT" in codes


class _MockHub:
    def call(self, messages, *, temperature: float, max_tokens: int):
        # Always return a minimal JSON with one issue and a suggested fix
        payload = {
            "issues": [{"question_id": "q5", "code": "LLM_CRITIQUE", "message": "Ngôn ngữ chưa rõ ràng"}],
            "suggested_fixes": [{"question_id": "q5", "patch": {"question_text": "Hãy tính 1 + 1"}, "reason": "Đơn giản, rõ ràng"}],
        }
        return json.dumps(payload, ensure_ascii=False), "mock"


def test_llm_critique_path_with_mock_hub():
    vt = ValidationTool(hub=_MockHub(), config={
        "enable_llm_critique": True,
        "auto_fix_once": False,
    })
    q = make_mcq("q5")
    res = vt.validate([q])
    assert any(i.get("code") == "LLM_CRITIQUE" for i in res.get("issues", []))
    assert any(s.get("question_id") == "q5" for s in res.get("suggested_fixes", []))


