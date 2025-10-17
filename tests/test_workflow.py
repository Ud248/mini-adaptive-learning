from typing import Any, Dict

from agent.workflow.agent_workflow import AgentWorkflow


class _MockRAG:
    def query(self, *, grade, skill, skill_name, topk_sgv, topk_sgk):
        return {
            "teacher_context": [{"id": "t1", "text": "Hướng dẫn cộng trừ đơn giản", "score": 0.9}],
            "textbook_context": [{"id": "b1", "text": "Q: 2 + 3 = ?\nA: 5", "score": 0.8}],
        }


class _MockGen:
    def __init__(self):
        self.calls = 0

    def generate(self, *, teacher_context, textbook_context, profile_student, constraints):
        self.calls += 1
        return {
            "questions": [
                {
                    "question_id": f"q{self.calls}",
                    "question_text": "2 + 3 bằng mấy?",
                    "question_type": "multiple_choice",
                    "answers": [
                        {"text": "5", "correct": True},
                        {"text": "4", "correct": False},
                        {"text": "6", "correct": False},
                        {"text": "7", "correct": False},
                    ],
                }
            ],
            "metadata": {"call": self.calls},
        }


class _MockVal:
    def __init__(self, approve_after: int = 1):
        self.approve_after = approve_after
        self.calls = 0

    def validate(self, questions, *, skill=None, teacher_context=None, textbook_context=None, grade=None):
        self.calls += 1
        if self.calls < self.approve_after:
            return {"status": "revise", "issues": [{"code": "DUMMY", "message": "revise"}]}
        return {"status": "approved", "issues": []}


def test_workflow_happy_path(monkeypatch):
    wf = AgentWorkflow()
    # monkeypatch tools
    wf.rag = _MockRAG()
    wf.generator = _MockGen()
    wf.validator = _MockVal(approve_after=1)

    out = wf.run(
        profile_student={"username": "hs1", "accuracy": 60},
        constraints={"grade": 1, "skill": "S5", "skill_name": "Mấy và mấy", "num_questions": 1},
    )
    assert out["metadata"]["validation"]["status"] == "approved"
    assert out["metadata"]["num_questions"] == 1


def test_workflow_regen_once(monkeypatch):
    wf = AgentWorkflow(config={"regen_limit": 2})
    wf.rag = _MockRAG()
    wf.generator = _MockGen()
    wf.validator = _MockVal(approve_after=2)  # first revise, then approve

    out = wf.run(
        profile_student={"username": "hs1", "accuracy": 60},
        constraints={"grade": 1, "skill": "S5", "skill_name": "Mấy và mấy", "num_questions": 1},
    )
    assert out["metadata"]["validation"]["status"] == "approved"
    assert out["metadata"]["regen_attempts"] >= 1



