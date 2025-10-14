import json
from typing import Any, Dict, List

import requests

from .provider_base import LLMProvider


class OllamaProvider(LLMProvider):
    def __init__(self, name: str, base_url: str, model: str, timeout_s: int = 15) -> None:
        super().__init__(name)
        self.base_url = base_url.rstrip("/")
        self.model = model
        self.timeout_s = timeout_s

    def generate(self, messages: List[Dict[str, str]], *, temperature: float, max_tokens: int) -> str:
        # Minimal chat wrapper for Ollama
        url = f"{self.base_url}/api/chat"
        payload = {"model": self.model, "messages": messages, "options": {"temperature": temperature, "num_predict": max_tokens}}
        resp = requests.post(url, json=payload, timeout=self.timeout_s)
        resp.raise_for_status()
        # Streaming can be enabled later; parse non-stream response
        data = resp.json()
        if isinstance(data, dict) and "message" in data:
            return data["message"].get("content", "")
        return json.dumps(data)


