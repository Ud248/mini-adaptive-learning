from typing import List, Optional, Dict, Any
from pydantic import BaseModel


class GenerateRequest(BaseModel):
    username: str
    skill: str
    skill_name: Optional[str] = None
    grade: int = 1
    num_questions: int = 6
    # New adaptive learning fields
    accuracy: Optional[float] = 60  # % correct answers (0-100)
    answered: Optional[float] = 70  # % answered (0-100)
    skipped: Optional[float] = 20   # % skipped (0-100)
    avg_response_time: Optional[float] = 30  # seconds per question


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


