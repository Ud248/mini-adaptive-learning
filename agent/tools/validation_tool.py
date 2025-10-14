from typing import Any, Dict, List


class ValidationTool:
    def __init__(self) -> None:
        pass

    def validate(self, questions: List[Dict[str, Any]], *, skill: str | None = None) -> Dict[str, Any]:
        # Minimal rule: ensure each MCQ has exactly one correct answer
        issues: List[Dict[str, str]] = []
        for q in questions:
            if q.get("question_type") == "mcq":
                correct_count = sum(1 for a in q.get("answers", []) if a.get("correct") is True)
                if correct_count != 1:
                    issues.append({"code": "MCQ_CORRECT_COUNT", "message": f"question {q.get('question_id','?')}: expected 1 correct answer"})
        status = "approved" if not issues else "revise"
        return {"status": status, "issues": issues, "confidence": 0.5 if issues else 0.9}


