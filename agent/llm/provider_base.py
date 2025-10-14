from abc import ABC, abstractmethod
from typing import Any, Dict, List, Tuple


class LLMProvider(ABC):
    """Abstract base class for LLM providers."""

    name: str

    def __init__(self, name: str) -> None:
        self.name = name

    @abstractmethod
    def generate(self, messages: List[Dict[str, str]], *, temperature: float, max_tokens: int) -> str:
        raise NotImplementedError


