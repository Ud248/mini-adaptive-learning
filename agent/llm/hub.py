import time
from typing import Dict, List, Tuple

from .provider_base import LLMProvider


class LLMHub:
    """Simple priority-based fallback hub.

    This is a minimal scaffold; replace with full implementation later.
    """

    def __init__(self, providers: List[LLMProvider]) -> None:
        self.providers = providers

    def call(self, messages: List[Dict[str, str]], *, temperature: float, max_tokens: int) -> Tuple[str, str]:
        last_err: Exception | None = None
        for provider in self.providers:
            try:
                output = provider.generate(messages, temperature=temperature, max_tokens=max_tokens)
                if not output:
                    raise RuntimeError("empty_output")
                return output, provider.name
            except Exception as e:  # noqa: BLE001
                last_err = e
                time.sleep(0.1)
                continue
        raise RuntimeError(f"LLM fallback exhausted: {last_err}")


