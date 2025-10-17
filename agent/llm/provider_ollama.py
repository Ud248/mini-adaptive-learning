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
        # Use /api/chat endpoint for messages format
        url = f"{self.base_url}/api/chat"
        payload = {
            "model": self.model, 
            "messages": messages, 
            "options": {
                "temperature": temperature, 
                "num_predict": max_tokens
            }
        }
        resp = requests.post(url, json=payload, timeout=self.timeout_s)
        resp.raise_for_status()
        
        # Parse streaming response (Ollama returns streaming by default)
        response_text = ""
        for line in resp.iter_lines():
            if line:
                try:
                    # Ensure proper UTF-8 decoding
                    line_str = line.decode('utf-8', errors='replace')
                    data = json.loads(line_str)
                    if data.get("message"):
                        content = data["message"].get("content", "")
                        if content:
                            response_text += content
                    if data.get("done"):
                        break
                except (json.JSONDecodeError, UnicodeDecodeError) as e:
                    print(f"Warning: Failed to parse line: {e}")
                    continue
        
        return response_text

    def healthcheck(self) -> bool:
        try:
            url = f"{self.base_url}/api/tags"
            resp = requests.get(url, timeout=min(3, self.timeout_s))
            resp.raise_for_status()
            return True
        except Exception:
            return False


