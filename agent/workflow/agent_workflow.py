from typing import Any, Dict

from agent.tools import RAGTool, TemplateTool, QuestionGenerationTool, ValidationTool
from agent.llm.hub import LLMHub


class AgentWorkflow:
    def __init__(self, hub: LLMHub | None = None) -> None:
        self.rag = RAGTool()
        self.templates = TemplateTool()
        self.hub = hub or LLMHub(providers=[])
        self.generator = QuestionGenerationTool(self.hub)
        self.validator = ValidationTool()

    def generate(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        rag = self.rag.query(
            grade=payload.get("grade"),
            skill=payload["skill"],
            skill_name=payload.get("skill_name"),
            topk_sgv=payload.get("topk_sgv", 5),
            topk_sgk=payload.get("topk_sgk", 20),
        )
        tmpl = self.templates.select(
            grade=payload.get("grade"),
            skill_id=payload["skill"],
            target=None,
            num_options=4,
        )
        gen = self.generator.generate(
            teacher_context=rag["teacher_context"],
            textbook_context=rag["textbook_context"],
            templates=tmpl["templates"],
            profile_student={"username": payload.get("username", "unknown"), "skill_id": payload["skill"]},
            constraints={"num_questions": payload.get("num_questions", 6), "vn_tone": True, "age_safe": True},
        )
        questions = gen.get("questions", [])
        report = self.validator.validate(questions, skill=payload.get("skill"))
        return {"questions": questions, "validation": report, **rag}


