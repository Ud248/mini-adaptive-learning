from typing import List, Optional
from pydantic import BaseModel


class GenerateRequest(BaseModel):
    username: str
    skill: str
    skill_name: Optional[str] = None
    num_questions: int = 6


class ValidateRequest(BaseModel):
    questions: list
    skill: Optional[str] = None


class RefineRequest(BaseModel):
    questions: list
    teacher_feedback: str
    constraints: dict


