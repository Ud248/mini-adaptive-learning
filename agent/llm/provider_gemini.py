from typing import Dict, List

import requests

from .provider_base import LLMProvider


class GeminiProvider(LLMProvider):
    """Minimal Google Gemini API adapter (REST v1beta generateContent).

    Note: expects an API key string. For production, prefer the official SDK and
    add safety settings, tools, and JSON schema constraints as needed.
    """

    def __init__(self, name: str, model: str, api_key: str, timeout_s: int = 12, base_url: str = "https://generativelanguage.googleapis.com") -> None:
        super().__init__(name)
        self.model = model
        self.api_key = api_key
        self.timeout_s = timeout_s
        self.base_url = base_url.rstrip("/")

    def _messages_to_gemini(self, messages: List[Dict[str, str]]) -> List[Dict[str, object]]:
        contents: List[Dict[str, object]] = []
        for m in messages:
            role = m.get("role", "user")
            text = m.get("content", "")
            # Gemini supports roles: user, model, system (system treated as user context here)
            if role not in {"user", "model"}:
                role = "user"
            contents.append({"role": role, "parts": [{"text": text}]})
        return contents

    def generate(self, messages: List[Dict[str, str]], *, temperature: float, max_tokens: int) -> str:
        url = f"{self.base_url}/v1beta/models/{self.model}:generateContent?key={self.api_key}"
        body = {
            "contents": self._messages_to_gemini(messages),
            "generationConfig": {
                "temperature": temperature,
                "maxOutputTokens": max_tokens,
            },
        }
        resp = requests.post(url, json=body, timeout=self.timeout_s)
        resp.raise_for_status()
        data = resp.json()
        # Parse primary candidate text
        try:
            candidates = data.get("candidates", [])
            if not candidates:
                return ""
            parts = candidates[0].get("content", {}).get("parts", [])
            if not parts:
                return ""
            return parts[0].get("text", "")
        except Exception:  # noqa: BLE001
            return ""


    def healthcheck(self) -> bool:
        try:
            url = f"{self.base_url}/v1beta/models/{self.model}"
            params = {"key": self.api_key}
            resp = requests.get(url, params=params, timeout=min(3, self.timeout_s))
            # Consider 200 OK responsive; some models may return 404 but endpoint still reachable
            return resp.status_code in (200, 404)
        except Exception:
            return False


