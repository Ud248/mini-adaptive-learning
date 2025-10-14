import pytest
from typing import Dict, List

from agent.llm.hub import LLMHub
from agent.llm.provider_base import LLMProvider


class FakeProvider(LLMProvider):
    def __init__(self, name: str, behavior: str = "success", output: str = "ok") -> None:
        super().__init__(name)
        self.behavior = behavior
        self.output = output
        self.calls = 0

    def generate(self, messages: List[Dict[str, str]], *, temperature: float, max_tokens: int) -> str:
        self.calls += 1
        if self.behavior == "raise":
            raise RuntimeError(f"{self.name}_boom")
        if self.behavior == "empty":
            return ""
        return self.output


def test_hub_returns_from_first_success_provider():
    p1 = FakeProvider("p1", behavior="success", output="A")
    p2 = FakeProvider("p2", behavior="success", output="B")
    hub = LLMHub([p1, p2])

    out, provider_name = hub.call([{"role": "user", "content": "hello"}], temperature=0.2, max_tokens=16)

    assert out == "A"
    assert provider_name == "p1"
    assert p1.calls == 1
    assert p2.calls == 0


def test_hub_fallbacks_when_first_raises():
    p1 = FakeProvider("p1", behavior="raise")
    p2 = FakeProvider("p2", behavior="success", output="B")
    hub = LLMHub([p1, p2])

    out, provider_name = hub.call([{"role": "user", "content": "hello"}], temperature=0.2, max_tokens=16)

    assert out == "B"
    assert provider_name == "p2"
    assert p1.calls == 1
    assert p2.calls == 1


def test_hub_fallbacks_when_first_returns_empty():
    p1 = FakeProvider("p1", behavior="empty")
    p2 = FakeProvider("p2", behavior="success", output="B")
    hub = LLMHub([p1, p2])

    out, provider_name = hub.call([{"role": "user", "content": "hello"}], temperature=0.2, max_tokens=16)

    assert out == "B"
    assert provider_name == "p2"
    assert p1.calls == 1
    assert p2.calls == 1


def test_hub_exhausts_when_all_fail():
    p1 = FakeProvider("p1", behavior="raise")
    p2 = FakeProvider("p2", behavior="empty")
    hub = LLMHub([p1, p2])

    with pytest.raises(RuntimeError) as exc:
        hub.call([{"role": "user", "content": "hello"}], temperature=0.2, max_tokens=16)

    msg = str(exc.value)
    assert "fallback exhausted" in msg.lower()
    assert p1.calls == 1
    assert p2.calls == 1


