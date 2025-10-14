from typing import Any, Dict, List


class TemplateTool:
    def __init__(self) -> None:
        pass

    def select(self, *, grade: int | None, skill_id: str, target: str | None = None, num_options: int = 4) -> Dict[str, Any]:
        # Return minimal sample templates; replace with full catalog later
        return {
            "templates": [
                {
                    "id": "mcq.addition.within10.v1",
                    "question_type": "mcq",
                    "skill": skill_id,
                    "grade": grade,
                    "constraints": {
                        "number_range": [0, 10],
                        "operation": "addition",
                        "carry_allowed": False,
                        "num_options": num_options,
                        "unique_correct": True,
                    },
                    "slots": {"a": {"type": "int", "range": [0, 9]}, "b": {"type": "int", "range": [0, 9]}},
                    "surface_forms": ["a + b = mấy?"],
                }
            ]
        }


