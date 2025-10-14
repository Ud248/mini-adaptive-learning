from typing import Any, Dict

# Placeholder: integrate with database/milvus/milvus_client.py later


class RAGTool:
    def __init__(self) -> None:
        pass

    def query(self, *, grade: int | None, skill: str, skill_name: str | None, topk_sgv: int = 5, topk_sgk: int = 20) -> Dict[str, Any]:
        # TODO: implement Milvus queries; return dummy structure for now
        return {
            "teacher_context": [],
            "textbook_context": [],
        }


