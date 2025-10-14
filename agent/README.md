ALQ-Agent skeleton

This module contains a minimal scaffold for the adaptive learning agent. Implement logic iteratively following ALQ-Agent-Spec.md.


LLM Hub configuration
---------------------

- Configure providers and hub behavior in `configs/agent.yaml` under `llm:`.
- Example excerpt:

```
llm:
  providers:
    - name: gpt_oss_ollama
      type: ollama
      base_url: http://localhost:11434
      model: gpt-oss:20b-cloud
      priority: 1
      timeout_s: 15
    - name: gemini
      type: google_gemini
      model: gemini-2.0-flash-lite
      api_key_env: GEMINI_API_KEY
      priority: 2
      timeout_s: 12
  retry: 1
  temperature_default: 0.2
  max_tokens: 1024
  circuit_breaker:
    failure_threshold: 3
    cooldown_s: 120
```

Environment variables
---------------------

- `GEMINI_API_KEY`: required for `google_gemini` providers (name configurable via `api_key_env`).
- Ensure the variable is present in your shell or `.env` before running the agent.

Logging
-------

- Enable basic debug logging in your entrypoint before invoking the agent:

```python
import logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
```

- To see more detailed hub activity (retries, circuit breaker decisions), raise the level:

```python
logging.getLogger("agent.llm").setLevel(logging.DEBUG)
```

