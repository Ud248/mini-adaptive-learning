# 🤖 ALQ-Agent Module

> **Adaptive Learning Question Agent** - Hệ thống AI Agent tự động sinh câu hỏi thích ứng theo kỹ năng yếu của học sinh tiểu học Việt Nam

## 📋 Giới thiệu

Module **agent** là trái tim của hệ thống Mini Adaptive Learning, đảm nhận vai trò:

- 🎯 **Sinh câu hỏi thông minh**: Tự động tạo câu hỏi phù hợp với trình độ và kỹ năng yếu của học sinh
- 📚 **RAG-powered**: Kết hợp kiến thức từ SGV (Sách Giáo Viên) và SGK (Sách Giáo Khoa) qua vector search
- ✅ **Validation tự động**: Kiểm định câu hỏi về mặt logic, toán học, ngôn ngữ với 4 bước validation
- 🔄 **Multi-LLM Hub**: Hỗ trợ nhiều LLM provider với cơ chế fallback, retry và circuit breaker
- 🎓 **Chuẩn chương trình VN**: Tuân thủ chuẩn kiến thức kỹ năng giáo dục tiểu học Việt Nam
- 📊 **Phân bổ độ khó thích ứng**: Tự động điều chỉnh độ khó dựa trên hiệu suất học sinh

## 🛠️ Tech Stack

### Core Dependencies
```
- Python 3.10+
- PyYAML (config management)
- Requests (HTTP client for LLM APIs)
```

### LLM Providers
- **Ollama** (local LLM, priority 1) - Gemma2:9b
- **Google Gemini** (cloud LLM, priority 2) - Gemini 2.0 Flash Lite
- Extensible cho OpenAI, Anthropic, etc.

### Vector Database
- **Milvus** (via `database/milvus/`)
- Vietnamese embedding model (via `database/embeddings/`)

### Related Services
- MongoDB (student profiles, question history)
- Quiz API (REST endpoints)

## 📦 Cài đặt

### 1. Install Dependencies

```bash
# From project root
pip install -r requirements.txt
```

### 2. Setup Vector Database

```bash
# Start Milvus (via Docker Compose)
cd volumes/milvus
docker-compose up -d

# Insert data to Milvus
python database/milvus/setup_milvus.py
python database/milvus/insert_data_milvus.py
```

### 3. Setup LLM Providers

**Option A: Ollama (Local)**
```bash
# Install Ollama: https://ollama.ai
# Pull model
ollama pull gemma2:9b

# Verify
curl http://localhost:11434/api/tags
```

**Option B: Google Gemini**
```bash
# Set API key
export GEMINI_API_KEY="your-api-key"
# Windows PowerShell
$env:GEMINI_API_KEY="your-api-key"
```

## ⚙️ Cấu hình

### Environment Variables

```bash
# .env file
GEMINI_API_KEY=your-google-api-key-here

# Milvus connection
MILVUS_HOST=localhost
MILVUS_PORT=19530

# MongoDB connection
MONGODB_URI=mongodb://localhost:27017
```

### Agent Configuration

File: `configs/agent.yaml`

```yaml
llm:
  providers:
    - name: gemma2:9b
      type: ollama
      base_url: OLLAMA_IP    # http://localhost:11434
      model: gemma2:9b
      priority: 1            # Lower = higher priority
      timeout_s: 15
    
    - name: gemini
      type: google_gemini
      model: gemini-2.0-flash-lite
      api_key_env: GEMINI_API_KEY
      priority: 2
      timeout_s: 15
  
  retry: 1                   # Retry per provider
  temperature_default: 0.2
  max_tokens: 1024
  circuit_breaker:
    failure_threshold: 3     # Open circuit after N failures
    cooldown_s: 120          # Cooldown period

rag:
  topk_sgv: 5                # Top-K teacher context
  topk_sgk: 20               # Top-K textbook context
  cache_ttl_s: 900           # Cache TTL

question_generation:
  batch_size: 4              # Questions per batch (3-5)
  temperature: 0.3           # Temperature for generation
  max_tokens: 2048           # Max tokens for generation
  retry_on_parse_error: 2    # Retry on JSON parse errors
  enforce_4_answers: true    # Force 4 options for multiple choice
  enable_teacher_summary: true              # Enable teacher context summarization
  teacher_summary_mode: llm_then_rule       # llm_only | rule_only | llm_then_rule
  teacher_summary_max_tokens: 400           # Max tokens for summary
  teacher_summary_max_words: 180            # Max words for summary

images:
  base_url: http://125.212.229.11:8888/    # Base URL for images

validation:
  min_len: 6                 # Min question length (chars)
  max_len: 180               # Max question length (chars)
  banned_words: ["tục tĩu", "bạo lực"]
  require_abcd_format: true  # Require ABCD format
  unique_options: true       # Unique answer options
  grade_numeric_range:
    grade1: [0, 100]         # Numeric range for grade 1
  enable_math_check: true    # Verify math calculations
  enable_llm_critique: false # Use LLM for critique
  auto_fix_once: true        # Auto-fix issues once

workflow:
  regen_limit: 2             # Max regeneration attempts
  min_score: 0.0             # Min RAG relevance score
  max_teacher_ctx: 5         # Max teacher context chunks
  max_textbook_ctx: 20       # Max textbook context chunks
```

## 🚀 Chạy Module

### Development Mode

```python
# Python API
from agent.workflow import AgentWorkflow

workflow = AgentWorkflow()

result = workflow.run(
    profile_student={
        "username": "student1",
        "accuracy": 0.5,
        "skill_id": "S5",
        "answered": 0.7,      # Tỷ lệ trả lời
        "skipped": 0.2,       # Tỷ lệ bỏ qua
        "avg_response_time": 45  # Thời gian trả lời TB (giây)
    },
    constraints={
        "grade": 1,
        "skill": "S5",
        "skill_name": "Mấy và mấy",
        "num_questions": 6
    }
)

print(result["questions"])
```

### Via REST API

```bash
# Start Quiz API server
cd backend/quiz_api
uvicorn main:app --host 0.0.0.0 --port 8000

# Generate questions
curl -X POST http://localhost:8000/agent/questions/generate \
  -H "Content-Type: application/json" \
  -d '{
    "student_id": "student1",
    "grade": 1,
    "skill": "S5",
    "skill_name": "Mấy và mấy",
    "num_questions": 6
  }'
```

### Run Tests

```bash
# Unit tests
pytest tests/test_question_generation_tool.py
pytest tests/test_rag_tool.py
pytest tests/test_validation_tool.py

# Integration test
pytest tests/test_workflow.py

# Test with coverage
pytest --cov=agent tests/
```

## 📁 Cấu trúc thư mục

```
agent/
├── __init__.py                    # Package initializer
│
├── llm/                           # 🧠 LLM Hub & Providers
│   ├── __init__.py
│   ├── hub.py                     # Multi-provider orchestration
│   ├── provider_base.py           # Abstract base class
│   ├── provider_ollama.py         # Ollama integration
│   └── provider_gemini.py         # Google Gemini integration
│
├── models/                        # 📊 Data Models
│   ├── __init__.py
│   └── types.py                   # TypedDict, Pydantic schemas
│
├── prompts/                       # 📝 Prompt Templates
│   ├── __init__.py
│   ├── generation_prompts.py      # Question generation prompts
│   ├── validation_prompts.py      # Validation critique prompts
│   └── refine_prompts.py          # Question refinement prompts
│
├── tools/                         # 🔧 Core Tools
│   ├── __init__.py
│   ├── _json_parser.py            # LLM output parser
│   ├── rag_tool.py                # Vector search & context retrieval
│   ├── question_generation_tool.py # Question generator
│   └── validation_tool.py         # Question validator
│
└── workflow/                      # 🔄 Orchestration
    ├── __init__.py
    └── agent_workflow.py          # Main workflow engine
```

### Chi tiết các thành phần

#### 🧠 LLM Hub (`llm/`)
- **hub.py**: Priority-based LLM orchestration với retry, circuit breaker, soft-gate
- **provider_base.py**: Abstract base class cho LLM providers
- **provider_ollama.py**: Ollama integration với healthcheck
- **provider_gemini.py**: Google Gemini integration

#### 📊 Models (`models/`)
- **types.py**: TypedDict, Pydantic schemas cho data models

#### 📝 Prompts (`prompts/`)
- **generation_prompts.py**: Question generation prompts với 4-step validation
- **validation_prompts.py**: Validation critique prompts
- **refine_prompts.py**: Question refinement prompts

#### 🔧 Tools (`tools/`)
- **rag_tool.py**: Truy vấn Milvus, rerank, merge context từ SGV + SGK, caching
- **question_generation_tool.py**: Sinh câu hỏi từ context + student profile, teacher context summarization
- **validation_tool.py**: Rule-based + math checks + optional LLM critique, auto-fix
- **_json_parser.py**: LLM output parser với error handling

#### 🔄 Workflow (`workflow/`)
- **agent_workflow.py**: Điều phối toàn bộ pipeline: RAG → Generate → Validate → Refine

## 🔌 API/Usage

### AgentWorkflow

```python
from agent.workflow import AgentWorkflow

workflow = AgentWorkflow()

# Generate questions
result = workflow.run(
    profile_student={
        "username": "student1",
        "accuracy": 0.5,         # Current accuracy (0-1)
        "skill_id": "S5",        # Weak skill
        "answered": 0.7,         # Tỷ lệ trả lời (0-1)
        "skipped": 0.2,          # Tỷ lệ bỏ qua (0-1)
        "avg_response_time": 45  # Thời gian trả lời TB (giây)
    },
    constraints={
        "grade": 1,              # Grade level
        "skill": "S5",           # Skill code
        "skill_name": "Mấy và mấy",  # Skill name
        "num_questions": 6       # Number of questions
    }
)

# Output structure
{
    "questions": [
        {
            "question_id": "q1_abc123",
            "question_text": "3 + 2 = ?",
            "question_type": "multiple_choice",  # true_false | multiple_choice | fill_blank
            "difficulty": "easy",                # easy | medium | hard
            "answers": [
                {"text": "3", "correct": false},
                {"text": "5", "correct": true},
                {"text": "4", "correct": false},
                {"text": "6", "correct": false}
            ],
            "explanation": "3 + 2 = 5",
            "provenance": {
                "teacher_ids": ["vec_1", "vec_2"],
                "textbook_ids": ["vec_10"],
                "provider": "gemma2:9b",
                "timestamp": "2025-10-22T10:30:00Z"
            }
        },
        # ... more questions
    ],
    "metadata": {
        "attempts": 1,
        "timings": {
            "gen_attempt_1": 1200,  # ms
            "val_attempt_1": 300
        },
        "validation": {
            "status": "approved",
            "issues": []
        },
        "provider_used": "llm_hub"
    }
}
```

### RAGTool (Standalone)

```python
from agent.tools import RAGTool

rag = RAGTool()

result = rag.query(
    grade=1,
    skill="S5",
    skill_name="Mấy và mấy",
    topk_sgv=5,   # Teacher context
    topk_sgk=20   # Textbook context
)

print(result["teacher_context"])  # SGV chunks
print(result["textbook_context"]) # SGK examples
```

### QuestionGenerationTool (Standalone)

```python
from agent.tools import QuestionGenerationTool
from agent.llm.hub import LLMHub

hub = LLMHub()
generator = QuestionGenerationTool(hub)

result = generator.generate(
    teacher_context=[...],
    textbook_context=[...],
    profile_student={...},
    constraints={...}
)

print(result["questions"])
```

### ValidationTool (Standalone)

```python
from agent.tools import ValidationTool

validator = ValidationTool()

report = validator.validate(
    questions=[...],
    skill="S5",
    teacher_context=[...],
    textbook_context=[...],
    grade=1
)

# report structure
{
    "status": "approved" | "revise",
    "issues": [
        {
            "code": "DUP_OPTION",
            "message": "question q1: duplicated answer options"
        }
    ],
    "suggested_fixes": [...],      # From LLM critique (if enabled)
    "applied_fixes": [...],        # Auto-applied fixes
    "confidence": 0.92,
    "validated_questions": [...],  # Questions after auto-fix
    "debug_flags": {
        "enable_llm_critique": false,
        "hub_attached": false,
        "critique_branch_executed": false
    }
}
```

## 🎯 Tính năng chính

### 1. Adaptive Difficulty Distribution (Phân bổ độ khó thích ứng)

Hệ thống tự động điều chỉnh độ khó câu hỏi dựa trên hiệu suất học sinh:

- **Accuracy < 50%**: 60% EASY, 30% MEDIUM, 10% HARD
- **Accuracy 50-70%**: 30% EASY, 50% MEDIUM, 20% HARD  
- **Accuracy > 70%**: 20% EASY, 30% MEDIUM, 50% HARD
- **Skipped > 30%**: Tạo câu hỏi rõ ràng hơn
- **Avg time > 60s**: Tạo câu hỏi ngắn gọn hơn

### 2. Teacher Context Summarization (Tóm tắt ngữ cảnh giáo viên)

Giảm noise và tối ưu prompt khi context quá dài:

- **Mode**: `llm_only` | `rule_only` | `llm_then_rule`
- **Max tokens**: 400 tokens
- **Max words**: 180 từ
- Fallback tự động nếu LLM summarization thất bại

### 3. Multi Question Types (Nhiều loại câu hỏi)

- **true_false**: 2 đáp án (Đúng/Sai)
- **multiple_choice**: 4 đáp án (1 đúng, 3 sai)
- **fill_blank**: 4 đáp án (điền vào chỗ trống)

### 4. 4-Step Validation Process (Quy trình 4 bước kiểm định)

1. **Tính toán đáp án đúng**: Giải bài toán thủ công
2. **Tạo các đáp án sai**: Hợp lý (sai số ±1, ±2)
3. **Xác nhận correct flag**: CHỈ 1 đáp án có `"correct": true`
4. **Double check**: Đếm số đáp án đúng/sai

### 5. Automatic Question Fixing (Tự động sửa lỗi)

- Sửa duplicate options
- Normalize text formatting
- Fix missing required fields
- Adjust answer count

### 6. Circuit Breaker & Retry Logic (Bảo vệ và thử lại)

- **Failure threshold**: 3 lỗi → mở circuit
- **Cooldown**: 120s trước khi thử lại
- **Retry per provider**: 1 lần
- **Temperature decay**: Giảm 0.1 mỗi retry

## 🔗 Kết nối Module Khác

### Dependencies

```python
# Internal dependencies
from database.milvus.milvus_client import MilvusClient
from database.embeddings.local_embedder import embed_text_quick
from database.mongodb.mongodb_client import MongoDBClient

# External APIs
# - Quiz API: POST /agent/questions/generate
# - SAINT Analysis: Student knowledge state
```

### Integration Points

1. **Database Layer**
   - `database/milvus/`: Vector search cho SGV/SGK
   - `database/mongodb/`: Student profiles, question history

2. **Backend Services**
   - `backend/quiz_api/`: REST API wrapper
   - `backend/saint_analysis/`: Student knowledge modeling

3. **Frontend**
   - `frontend/quiz-app/`: UI hiển thị câu hỏi

### Workflow Integration

```
User (Frontend)
    ↓
Quiz API (backend/quiz_api/)
    ↓
AgentWorkflow (agent/)
    ↓
├─→ RAGTool → Milvus (database/milvus/)
├─→ LLMHub → Ollama/Gemini (agent/llm/)
└─→ ValidationTool → [rule checks + math checks]
    ↓
MongoDB (database/mongodb/) [save history]
    ↓
Response → Frontend
```

## 🐛 Troubleshooting

### 1. LLM Connection Issues

**Error**: `LLM_FALLBACK_EXHAUSTED`

```bash
# Check Ollama
curl http://localhost:11434/api/tags

# Check Gemini API key
echo $GEMINI_API_KEY

# Check provider config in configs/agent.yaml
# Verify priority, timeout_s, base_url
```

### 2. Empty Context from RAG

**Error**: `teacher_context` or `textbook_context` is empty

```bash
# Verify Milvus collections
python -c "
from database.milvus.milvus_client import MilvusClient
client = MilvusClient()
print(client.get_collection_stats('sgv_collection'))
print(client.get_collection_stats('baitap_collection'))
"

# Check if data was inserted
python database/mongodb/insert_data_mongodb.py
python database/milvus/insert_data_milvus.py
```

### 3. Validation Always Fails

**Issue**: Questions keep getting rejected

```yaml
# In configs/agent.yaml, adjust validation:
validation:
  enable_math_check: false   # Disable if too strict
  enable_llm_critique: false
  auto_fix_once: true
  min_len: 5                 # Reduce min length
  max_len: 200               # Increase max length

workflow:
  regen_limit: 3             # Increase retry limit
```

### 4. Slow Generation

**Issue**: Generation takes > 10 seconds

```yaml
# Optimize config:
rag:
  topk_sgv: 3                # Reduce context size
  topk_sgk: 10

question_generation:
  batch_size: 3              # Generate fewer questions per batch
  max_tokens: 1024           # Reduce token limit
  enable_teacher_summary: true
  teacher_summary_mode: rule_only  # Faster than LLM

llm:
  timeout_s: 10              # Reduce timeout
```

### 5. Circuit Breaker Triggered

**Error**: Provider blocked by circuit breaker

```bash
# Wait for cooldown_s (default 120s)
# Or restart application to reset

# Adjust thresholds in configs/agent.yaml:
llm:
  circuit_breaker:
    failure_threshold: 5  # Increase tolerance
    cooldown_s: 60        # Reduce cooldown
```

### 6. JSON Parse Errors

**Error**: `ParseError: Could not extract valid JSON`

```yaml
# In configs/agent.yaml:
question_generation:
  retry_on_parse_error: 3  # Increase retry
  temperature: 0.2         # Lower temperature for more deterministic output
```

### 7. Math Validation Failures

**Issue**: Correct answers marked as wrong

```yaml
# Check validation logic in agent/tools/validation_tool.py
# Adjust grade_numeric_range:
validation:
  grade_numeric_range:
    grade1: [0, 100]  # Adjust range for grade
  enable_math_check: true
```

### 8. Teacher Context Too Long

**Issue**: Context exceeds token limit

```yaml
# Enable teacher context summarization:
question_generation:
  enable_teacher_summary: true
  teacher_summary_mode: llm_then_rule  # or rule_only for speed
  teacher_summary_max_tokens: 400
  teacher_summary_max_words: 180

# Or reduce context size:
rag:
  topk_sgv: 3  # Reduce from 5
```

### 9. Wrong Answer Marked as Correct

**Issue**: "correct" flag doesn't match calculation result

```python
# This is prevented by 4-step validation in prompts
# Check generation_prompts.py SYSTEM_PROMPT for validation steps
# If still happening, increase temperature for more careful generation:
question_generation:
  temperature: 0.2  # Lower temperature = more deterministic
  retry_on_parse_error: 3  # More retries
```

---

## 📚 Tài liệu tham khảo

- [Database README](../database/README.md) - Database setup guide
- [Quiz API README](../backend/quiz_api/README.md) - REST API docs
- [Configs README](../configs/README.md) - Configuration guide

---

## 🎯 Roadmap

- [x] 4-step validation process
- [x] Adaptive difficulty distribution
- [x] Teacher context summarization
- [x] Multi question types (true_false, multiple_choice, fill_blank)
- [x] Circuit breaker & retry logic
- [x] Automatic question fixing
- [ ] Refine tool với feedback giáo viên
- [ ] A/B testing framework cho prompts
- [ ] Multi-language support (English, etc.)
- [ ] Real-time streaming generation
- [ ] Question difficulty prediction model

---

**Maintainer**: Mini Adaptive Learning Team  
**Last Updated**: October 22, 2025
