# ⚙️ Configs Module

> Central configuration management cho Mini Adaptive Learning system - YAML-based configuration cho AI Agent

## 📋 Giới thiệu

Folder **configs** chứa các file cấu hình tập trung cho toàn bộ hệ thống, đặc biệt là:

- 🤖 **LLM Configuration**: Multi-provider setup với fallback và circuit breaker
- 🔍 **RAG Settings**: Vector search parameters cho Milvus
- 📝 **Question Generation**: AI agent generation parameters
- ✅ **Validation Rules**: Question quality checks
- 🔄 **Workflow Settings**: Agent orchestration parameters

## 📁 Cấu trúc

```
configs/
├── agent.yaml          # 🎯 Main AI Agent configuration
└── README.md           # 📖 This file
```

## 🔧 Configuration Files

### agent.yaml

File cấu hình chính cho AI Agent module với các sections:

#### 1. LLM Configuration 🤖

```yaml
llm:
  providers:
    - name: gpt_oss_ollama          # Provider name
      type: ollama                   # Provider type
      base_url: http://localhost:11434  # API endpoint
      model: gemma2:9b               # Model name
      priority: 1                    # Lower = higher priority
      timeout_s: 15                  # Request timeout
    
    - name: gemini
      type: google_gemini
      model: gemini-2.0-flash-lite
      api_key_env: GOOGLE_API_KEY    # Env var name for API key
      priority: 2                    # Fallback provider
      timeout_s: 15
  
  retry: 1                           # Retry per provider
  temperature_default: 0.2           # Default temperature
  max_tokens: 1024                   # Default max tokens
  
  circuit_breaker:
    failure_threshold: 3             # Open circuit after N failures
    cooldown_s: 120                  # Cooldown before retry
```

**Providers Supported:**
- `ollama`: Local LLM (Ollama)
- `google_gemini`: Google Gemini API
- `openai`: OpenAI API (extensible)

**Priority System:**
- Lower number = higher priority
- Fallback automatically if higher priority fails
- Circuit breaker prevents repeated failures

**Circuit Breaker:**
- Tracks failures per provider
- Opens circuit after threshold
- Cooldown period before retry
- Prevents cascading failures

#### 2. RAG Configuration 🔍

```yaml
rag:
  topk_sgv: 5              # Top-K teacher guide contexts
  topk_sgk: 20             # Top-K textbook contexts
  cache_ttl_s: 900         # Cache TTL (15 minutes)
```

**Parameters:**
- `topk_sgv`: Number of SGV (Sách Giáo Viên) chunks to retrieve
- `topk_sgk`: Number of SGK (Sách Giáo Khoa) examples to retrieve
- `cache_ttl_s`: Cache time-to-live for RAG results

**Usage:**
- Higher topk = more context but slower
- Lower topk = faster but less context
- Cache reduces repeated Milvus queries

#### 3. Question Generation 📝

```yaml
question_generation:
  batch_size: 4                      # Questions per batch (3-5)
  temperature: 0.3                   # LLM temperature
  max_tokens: 2048                   # Max tokens for generation
  retry_on_parse_error: 2            # Retry if JSON parse fails
  enforce_4_answers: true            # Force 4 options (A/B/C/D)
  
  enable_teacher_summary: true       # Summarize teacher context
  teacher_summary_mode: llm_then_rule  # Summarization strategy
  teacher_summary_max_tokens: 400    # Max tokens for summary
  teacher_summary_max_words: 180     # Max words for summary
```

**Parameters:**
- `batch_size`: Number of questions generated per batch
  - Too high: May exceed token limit
  - Too low: More API calls needed
  - Recommended: 3-5

- `temperature`: Controls randomness
  - 0.0: Deterministic
  - 0.3: Balanced (recommended for questions)
  - 1.0: Very creative

- `enforce_4_answers`: Vietnamese standard (A/B/C/D format)

**Teacher Summary Modes:**
- `llm_only`: Use LLM to summarize
- `rule_only`: Use rule-based extraction
- `llm_then_rule`: Try LLM first, fallback to rules

#### 4. Image Configuration 🖼️

```yaml
images:
  base_url: http://125.212.229.11:8888/
```

**SeaweedFS Integration:**
- Base URL for image storage
- Images prefixed with `@` in responses
- Fallback handling for missing images

#### 5. Validation Rules ✅

```yaml
validation:
  min_len: 6                         # Min question length
  max_len: 180                       # Max question length
  banned_words: ["tục tĩu", "bạo lực"]  # Inappropriate words
  require_abcd_format: true          # Require A/B/C/D format
  unique_options: true               # No duplicate answers
  
  grade_numeric_range:
    grade1: [0, 100]                 # Valid number range per grade
  
  enable_math_check: true            # Verify math calculations
  enable_llm_critique: false         # Use LLM for validation
  auto_fix_once: true                # Auto-fix minor issues
  critique_provider: ""              # LLM provider for critique
```

**Rule-based Checks:**
- Length constraints
- Banned words filter
- Format requirements (A/B/C/D)
- Unique options check

**Math Validation:**
- Parse mathematical expressions
- Calculate correct answers
- Verify answer correctness
- Grade-appropriate numbers

**Auto-fix:**
- Fix duplicate options
- Randomize option order
- Trim excessive whitespace
- One-time fix only

#### 6. Workflow Settings 🔄

```yaml
workflow:
  regen_limit: 2                     # Max regeneration attempts
  min_score: 0.0                     # Min RAG relevance score
  max_teacher_ctx: 5                 # Max teacher contexts used
  max_textbook_ctx: 20               # Max textbook contexts used
  log_level: INFO                    # Logging level
```

**Workflow Parameters:**
- `regen_limit`: How many times to regenerate if validation fails
  - Higher: More chances for good questions
  - Lower: Faster but may have quality issues

- `min_score`: Filter RAG results by relevance
  - 0.0: Accept all results
  - 0.5: Medium threshold
  - 0.8: High quality only

- Context limits: Control token usage and quality
  - More context = better questions but slower
  - Less context = faster but may lack depth

## 🚀 Usage

### Load Configuration

```python
# In Python code
import yaml
import os

def load_config():
    config_path = os.path.join(os.getcwd(), "configs", "agent.yaml")
    with open(config_path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)

config = load_config()
```

### Access Configuration

```python
# LLM settings
llm_config = config["llm"]
providers = llm_config["providers"]
retry = llm_config["retry"]

# RAG settings
rag_config = config["rag"]
topk_sgv = rag_config["topk_sgv"]

# Question generation settings
gen_config = config["question_generation"]
batch_size = gen_config["batch_size"]
temperature = gen_config["temperature"]

# Validation settings
val_config = config["validation"]
enable_math_check = val_config["enable_math_check"]

# Workflow settings
workflow_config = config["workflow"]
regen_limit = workflow_config["regen_limit"]
```

### Example: AgentWorkflow

```python
from agent.workflow import AgentWorkflow

# Loads configs/agent.yaml automatically
workflow = AgentWorkflow()

# Or pass custom config
custom_config = {
    "regen_limit": 3,
    "min_score": 0.5,
    "max_teacher_ctx": 10
}
workflow = AgentWorkflow(config=custom_config)
```

### Example: LLMHub

```python
from agent.llm.hub import LLMHub

# Loads LLM config from agent.yaml
hub = LLMHub()

# Or pass custom config
custom_config = {
    "llm": {
        "providers": [
            {
                "name": "ollama",
                "type": "ollama",
                "base_url": "http://localhost:11434",
                "model": "llama2",
                "priority": 1
            }
        ],
        "retry": 2
    }
}
hub = LLMHub(cfg=custom_config)
```

## 🔧 Configuration Best Practices

### 1. Provider Priority

```yaml
# Fast local model first
- name: ollama
  type: ollama
  priority: 1

# Cloud fallback
- name: gemini
  type: google_gemini
  priority: 2
```

### 2. Temperature Settings

```yaml
# Question generation: moderate creativity
question_generation:
  temperature: 0.3

# Validation: deterministic
validation:
  enable_llm_critique: true
  # Use temperature: 0.0 in critique calls
```

### 3. Token Limits

```yaml
# Balance quality and cost
question_generation:
  batch_size: 4          # 4 questions
  max_tokens: 2048       # ~500 tokens per question

# RAG context
workflow:
  max_teacher_ctx: 5     # ~500 tokens
  max_textbook_ctx: 20   # ~2000 tokens
# Total: ~2500 tokens input
```

### 4. Retry Strategy

```yaml
# LLM level
llm:
  retry: 1               # Retry once per provider

# Generation level
question_generation:
  retry_on_parse_error: 2  # Retry if JSON fails

# Workflow level
workflow:
  regen_limit: 2         # Regenerate if validation fails
```

### 5. Development vs Production

**Development** (`agent.yaml`):
```yaml
llm:
  providers:
    - name: ollama
      base_url: http://localhost:11434
      priority: 1

workflow:
  log_level: DEBUG
  regen_limit: 2
```

**Production** (`agent.prod.yaml`):
```yaml
llm:
  providers:
    - name: gemini
      priority: 1
    - name: ollama_backup
      priority: 2

workflow:
  log_level: WARNING
  regen_limit: 3
  
circuit_breaker:
  failure_threshold: 5
  cooldown_s: 300
```

## 🎯 Configuration Scenarios

### Scenario 1: High Quality Questions

```yaml
question_generation:
  batch_size: 3          # Smaller batch for focus
  temperature: 0.2       # More deterministic
  max_tokens: 3072       # More detailed

workflow:
  regen_limit: 3         # More retry attempts
  max_teacher_ctx: 10    # More context
  
validation:
  enable_llm_critique: true  # Additional validation
  enable_math_check: true
```

### Scenario 2: Fast Generation

```yaml
question_generation:
  batch_size: 5          # Larger batch
  temperature: 0.4       # More creative
  max_tokens: 1536       # Less detailed

workflow:
  regen_limit: 1         # Less retries
  max_teacher_ctx: 3     # Less context
  
validation:
  enable_llm_critique: false  # Faster validation
```

### Scenario 3: Cost Optimization

```yaml
llm:
  providers:
    - name: ollama         # Free local model
      priority: 1
    - name: gemini         # Paid API fallback
      priority: 2

question_generation:
  batch_size: 5          # Fewer API calls
  enable_teacher_summary: true
  teacher_summary_mode: rule_only  # No LLM for summary

workflow:
  regen_limit: 1         # Less regeneration
```

## 🐛 Troubleshooting

### 1. LLM Connection Issues

**Problem**: `LLM_FALLBACK_EXHAUSTED`

```yaml
# Check provider configuration
llm:
  providers:
    - name: ollama
      base_url: http://localhost:11434  # Correct URL?
      timeout_s: 30                      # Increase timeout
```

```bash
# Test Ollama
curl http://localhost:11434/api/tags

# Test Gemini
echo $GOOGLE_API_KEY
```

### 2. Circuit Breaker Always Open

**Problem**: Provider keeps getting blocked

```yaml
# Increase threshold or decrease cooldown
circuit_breaker:
  failure_threshold: 5   # Increase from 3
  cooldown_s: 60         # Decrease from 120
```

### 3. Questions Too Short/Long

**Problem**: Generated questions don't meet requirements

```yaml
# Adjust generation parameters
question_generation:
  max_tokens: 2048       # Increase for longer questions

# Adjust validation
validation:
  min_len: 10            # Increase minimum
  max_len: 200           # Increase maximum
```

### 4. Math Questions Wrong

**Problem**: Math validation fails

```yaml
# Check grade ranges
validation:
  grade_numeric_range:
    grade1: [0, 100]     # Appropriate for grade 1?
  enable_math_check: true

# Or disable if too strict
validation:
  enable_math_check: false
```

### 5. RAG Returns Nothing

**Problem**: Empty context from vector search

```yaml
# Lower relevance threshold
workflow:
  min_score: 0.0         # Accept all results

# Increase retrieval
rag:
  topk_sgv: 10           # Increase from 5
  topk_sgk: 30           # Increase from 20
```

### 6. Generation Too Slow

**Problem**: Takes too long to generate

```yaml
# Reduce context
workflow:
  max_teacher_ctx: 3     # Reduce from 5
  max_textbook_ctx: 10   # Reduce from 20

# Reduce batch size
question_generation:
  batch_size: 3          # Reduce from 4

# Reduce timeout
llm:
  providers:
    - timeout_s: 10      # Reduce from 15
```

### 7. Config File Not Found

**Problem**: `FileNotFoundError: agent.yaml`

```bash
# Check current directory
pwd

# Config should be at: ./configs/agent.yaml
ls configs/agent.yaml

# Or specify full path in code
config_path = os.path.join(os.getcwd(), "configs", "agent.yaml")
```

## 📊 Configuration Template

### Minimal Configuration

```yaml
llm:
  providers:
    - name: ollama
      type: ollama
      base_url: http://localhost:11434
      model: gemma2:9b
      priority: 1

rag:
  topk_sgv: 5
  topk_sgk: 20

question_generation:
  batch_size: 4
  temperature: 0.3

validation:
  enable_math_check: true

workflow:
  regen_limit: 2
```

### Full Production Configuration

See `agent.yaml` in this directory for complete example.

## 📚 Tài liệu tham khảo

- [Agent Module README](../agent/README.md) - How agent uses configs
- [LLM Hub Documentation](../agent/llm/README.md) - Provider setup
- [RAG Tool Documentation](../agent/tools/README.md) - RAG parameters
- [Workflow Documentation](../agent/workflow/README.md) - Workflow settings
- [YAML Specification](https://yaml.org/spec/1.2/spec.html) - YAML syntax

---

## 🎯 Quick Reference

| Section | Key Parameters | Default | Description |
|---------|---------------|---------|-------------|
| **LLM** | `retry` | 1 | Retry per provider |
| | `temperature_default` | 0.2 | Default temperature |
| | `failure_threshold` | 3 | Circuit breaker threshold |
| **RAG** | `topk_sgv` | 5 | Teacher contexts |
| | `topk_sgk` | 20 | Textbook contexts |
| | `cache_ttl_s` | 900 | Cache duration |
| **Generation** | `batch_size` | 4 | Questions per batch |
| | `temperature` | 0.3 | Generation temperature |
| | `max_tokens` | 2048 | Max generation tokens |
| **Validation** | `min_len` | 6 | Min question length |
| | `max_len` | 180 | Max question length |
| | `enable_math_check` | true | Math verification |
| **Workflow** | `regen_limit` | 2 | Max regenerations |
| | `max_teacher_ctx` | 5 | Max teacher contexts |
| | `max_textbook_ctx` | 20 | Max textbook contexts |

---

**Maintainer**: Mini Adaptive Learning Team  
**Last Updated**: October 17, 2025
