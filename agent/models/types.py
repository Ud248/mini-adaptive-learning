from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any


@dataclass
class AnswerOption:
    text: str
    correct: bool


@dataclass
class Question:
    grade: Optional[int]
    skill: str
    skill_name: Optional[str]
    subject: str
    question_id: str
    question_type: str
    question_text: str
    answers: List[AnswerOption]
    explanation: Optional[str] = None
    image_question: str = ""
    image_answer: str = ""
    provenance: Dict[str, Any] = field(default_factory=dict)
    validation: Dict[str, Any] = field(default_factory=dict)
    version: int = 1


@dataclass
class ContextChunk:
    id: str
    text: str
    source: str
    lesson: str
    score: float


@dataclass
class ValidationIssue:
    code: str
    message: str


@dataclass
class ValidationReport:
    status: str
    issues: List[ValidationIssue]
    confidence: float


