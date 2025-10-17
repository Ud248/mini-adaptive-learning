from typing import List, Optional, Dict, Any
from pydantic import BaseModel


class GenerateRequest(BaseModel):
    username: str
    skill: str
    skill_name: Optional[str] = None
    grade: int = 1
    num_questions: int = 6


class ValidateRequest(BaseModel):
    questions: List[Dict[str, Any]]
    skill: Optional[str] = None
    grade: int = 1
    teacher_context: Optional[List[Dict[str, Any]]] = None
    textbook_context: Optional[List[Dict[str, Any]]] = None


class RefineRequest(BaseModel):
    questions: list
    teacher_feedback: str
    constraints: dict


