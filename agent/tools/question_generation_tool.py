from typing import Any, Dict, List

from agent.llm.hub import LLMHub


class QuestionGenerationTool:
    def __init__(self, hub: LLMHub) -> None:
        self.hub = hub

    def generate(self, *, teacher_context: List[Dict[str, Any]], textbook_context: List[Dict[str, Any]], templates: List[Dict[str, Any]], profile_student: Dict[str, Any], constraints: Dict[str, Any]) -> Dict[str, Any]:
        # Minimal stub: return empty list; integrate prompting later
        return {"questions": []}


