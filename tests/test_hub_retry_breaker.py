import time
from typing import Dict, List, Optional

import pytest

from agent.llm.hub import LLMHub
from agent.llm.provider_base import LLMProvider


class FlakyProvider(LLMProvider):
    def __init__(self, name: str, fail_times: int, output: str = "ok") -> None:
        super().__init__(name)
        self.fail_times = fail_times
        self.output = output
        self.calls = 0

    def generate(self, messages: List[Dict[str, str]], *, temperature: float, max_tokens: int) -> str:
        self.calls += 1
        if self.calls <= self.fail_times:
            raise RuntimeError("boom")
        return self.output


def test_retry_temperature_decay(monkeypatch):
    # Capture temps used
    used_temps: List[float] = []

    class TempSpyProvider(LLMProvider):
        def __init__(self) -> None:
            super().__init__("spy")
            self.calls = 0

        def generate(self, messages: List[Dict[str, str]], *, temperature: float, max_tokens: int) -> str:
            used_temps.append(temperature)
            self.calls += 1
            if self.calls < 2:
                raise RuntimeError("fail once")
            return "ok"

    hub = LLMHub({"llm": {"retry": 1}} , providers=[TempSpyProvider()])
    out, prov = hub.call([{"role": "user", "content": "hi"}], temperature=0.3, max_tokens=16)
    assert out == "ok"
    assert used_temps[0] == pytest.approx(0.3)
    assert used_temps[1] == pytest.approx(0.2)


def test_circuit_breaker_opens_and_cools_down(monkeypatch):
    # Freeze time
    fake_time = [1000.0]

    def fake_time_func():
        return fake_time[0]

    monkeypatch.setattr(time, "time", fake_time_func)

    cfg = {"llm": {"retry": 0, "circuit_breaker": {"failure_threshold": 2, "cooldown_s": 10}}}
    p1 = FlakyProvider("p1", fail_times=3)
    p2 = FlakyProvider("p2", fail_times=0, output="ok")
    hub = LLMHub(cfg, providers=[p1, p2])

    # First two attempts on p1 fail and open breaker; hub should use p2
    out, prov = hub.call([{"role": "user", "content": "hi"}], temperature=0.2, max_tokens=8)
    assert out == "ok"
    assert prov == "p2"

    # During cooldown, p1 is skipped
    out2, prov2 = hub.call([{"role": "user", "content": "hi"}], temperature=0.2, max_tokens=8)
    assert prov2 == "p2"

    # Advance time past cooldown, half-open allows retry on p1 which fails again and reopens
    fake_time[0] += 11
    with pytest.raises(RuntimeError):
        # Both providers will be tried; p1 fails (reopens), then p2 returns empty to force fail path
        hub2 = LLMHub(cfg, providers=[FlakyProvider("p1", fail_times=10), FlakyProvider("p2", fail_times=10)])
        hub2.call([{"role": "user", "content": "hi"}], temperature=0.2, max_tokens=8)


def test_warmup_healthcheck_opens_provider(monkeypatch):
    class BadHealthProvider(LLMProvider):
        def __init__(self, name: str) -> None:
            super().__init__(name)

        def generate(self, messages: List[Dict[str, str]], *, temperature: float, max_tokens: int) -> str:
            return "should_not_be_called"

        def healthcheck(self) -> bool:
            return False

    cfg = {"llm": {"retry": 0, "circuit_breaker": {"failure_threshold": 1, "cooldown_s": 60}}}
    bad = BadHealthProvider("bad")
    good = FlakyProvider("good", fail_times=0, output="ok")
    hub = LLMHub(cfg, providers=[bad, good])

    out, prov = hub.call([{"role": "user", "content": "hi"}], temperature=0.2, max_tokens=8)
    assert prov == "good"


