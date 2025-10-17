import os
import time
from typing import Any, Callable, Dict, List, Optional, Tuple

from .provider_base import LLMProvider


class LLMHub:
    """Priority-based fallback hub with retry, soft-gate, and circuit breaker."""

    def __init__(self, cfg: Optional[Dict[str, Any]] = None, providers: Optional[List[LLMProvider]] = None) -> None:
        # Backward compatibility: allow passing providers list as first positional arg
        self.legacy_mode = False
        if isinstance(cfg, list) and all(hasattr(p, "generate") for p in cfg):  # type: ignore[arg-type]
            providers = cfg  # type: ignore[assignment]
            cfg = {}
            self.legacy_mode = True
        self.cfg = cfg or {}
        self.retry = int(self.cfg.get("llm", {}).get("retry", 1))
        cb = self.cfg.get("llm", {}).get("circuit_breaker", {})
        self.failure_threshold = int(cb.get("failure_threshold", 3))
        self.cooldown_s = int(cb.get("cooldown_s", 120))
        self.fail_counts: Dict[str, int] = {}
        self.open_until: Dict[str, float] = {}

        self.providers: List[LLMProvider] = providers or self._build_providers_from_cfg(self.cfg)

        # Warmup healthcheck
        now = time.time()
        for p in self.providers:
            try:
                ok = p.healthcheck()
            except Exception:  # noqa: BLE001
                ok = False
            if not ok:
                self.open_until[p.name] = now + self.cooldown_s

    def _is_open(self, name: str) -> bool:
        until = self.open_until.get(name)
        if until is None:
            return False
        if time.time() >= until:
            # half-open: allow next attempt, reset counter
            del self.open_until[name]
            self.fail_counts[name] = 0
            return False
        return True

    def _record_failure(self, name: str) -> None:
        cnt = self.fail_counts.get(name, 0) + 1
        self.fail_counts[name] = cnt
        if cnt >= self.failure_threshold:
            self.open_until[name] = time.time() + self.cooldown_s

    def _record_success(self, name: str) -> None:
        self.fail_counts[name] = 0
        self.open_until.pop(name, None)

    def call(
        self,
        messages: List[Dict[str, str]],
        *,
        temperature: float,
        max_tokens: int,
        soft_gate: Optional[Callable[[str], bool]] = None,
    ) -> Tuple[str, str]:
        last_err: Optional[Exception] = None
        providers = sorted(self.providers, key=lambda p: getattr(p, "priority", 999))
        for p in providers:
            if self._is_open(p.name):
                continue
            attempt_count = 1 if self.legacy_mode else (self.retry + 1)
            for attempt in range(attempt_count):
                t = max(0.0, temperature - 0.1 * attempt)
                try:
                    output = p.generate(messages, temperature=t, max_tokens=max_tokens)
                    if not output:
                        raise RuntimeError("empty_output")
                    if soft_gate and not soft_gate(output):
                        raise RuntimeError("soft_gate_reject")
                    self._record_success(p.name)
                    return output, p.name
                except Exception as e:  # noqa: BLE001
                    last_err = e
                    self._record_failure(p.name)
                    time.sleep(min(0.2 + 0.1 * attempt, 0.5))
                    continue
        if self.legacy_mode:
            raise RuntimeError(f"LLM fallback exhausted: {last_err}")
        raise RuntimeError(f"LLM_FALLBACK_EXHAUSTED: {last_err}")

    def _build_providers_from_cfg(self, cfg: Dict[str, Any]) -> List[LLMProvider]:
        from .provider_ollama import OllamaProvider
        from .provider_gemini import GeminiProvider

        out: List[LLMProvider] = []
        llm_cfg = cfg.get("llm", {})
        for item in llm_cfg.get("providers", []):
            t = item.get("type")
            name = item["name"]
            priority = item.get("priority", 999)
            timeout_s = item.get("timeout_s", 15)

            if t == "ollama":
                # Support both direct URL and environment variable
                base_url_raw = item["base_url"]
                # Try to resolve as environment variable first
                base_url = os.getenv(base_url_raw, base_url_raw)
                p = OllamaProvider(name=name, base_url=base_url, model=item["model"], timeout_s=timeout_s)
            elif t == "google_gemini":
                api_key_env = item.get("api_key_env", "GEMINI_API_KEY")
                api_key = os.getenv(api_key_env, "")
                if not api_key:
                    raise RuntimeError(f"Missing API key for provider '{name}' in env {api_key_env}")
                p = GeminiProvider(name=name, model=item["model"], api_key=api_key, timeout_s=timeout_s)
            else:
                raise ValueError(f"Unknown provider type: {t}")

            setattr(p, "priority", priority)
            out.append(p)
        return out


