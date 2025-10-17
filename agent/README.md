# 🤖 ALQ-Agent Module

> **Adaptive Learning Question Agent** - Hệ thống AI Agent tự động sinh câu hỏi thích ứng theo kỹ năng yếu của học sinh tiểu học Việt Nam

## 📋 Giới thiệu

Module **agent** là trái tim của hệ thống Mini Adaptive Learning, đảm nhận vai trò:

- 🎯 **Sinh câu hỏi thông minh**: Tự động tạo câu hỏi phù hợp với trình độ và kỹ năng yếu của học sinh
- 📚 **RAG-powered**: Kết hợp kiến thức từ SGV (Sách Giáo Viên) và SGK (Sách Giáo Khoa) qua vector search
- ✅ **Validation tự động**: Kiểm định câu hỏi về mặt logic, toán học, ngôn ngữ trước khi xuất
- 🔄 **Multi-LLM Hub**: Hỗ trợ nhiều LLM provider với cơ chế fallback, retry và circuit breaker
- 🎓 **Chuẩn chương trình VN**: Tuân thủ chuẩn kiến thức kỹ năng giáo dục tiểu học Việt Nam

## 🛠️ Tech Stack

### Core Dependencies
```
- Python 3.10+
- LangChain (optional, for prompt templates)
- PyYAML (config management)
- Requests (HTTP client for LLM APIs)
```

### LLM Providers
- **Ollama** (local LLM, priority 1)
- **Google Gemini** (cloud LLM, priority 2)
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
python database/milvus/insert_sgk_to_milvus.py
python database/milvus/insert_sgv_to_milvus.py
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
    - name: gpt_oss_ollama
      type: ollama
      base_url: http://localhost:11434
      model: gemma2:9b
      priority: 1         # Lower = higher priority
      timeout_s: 15
    
    - name: gemini
      type: google_gemini
      model: gemini-2.0-flash-lite
      api_key_env: GEMINI_API_KEY
      priority: 2
      timeout_s: 15
  
  retry: 1                # Retry per provider
  circuit_breaker:
    failure_threshold: 3  # Open circuit after N failures
    cooldown_s: 120       # Cooldown period

rag:
  topk_sgv: 5             # Top-K teacher context
  topk_sgk: 20            # Top-K textbook context
  cache_ttl_s: 900        # Cache TTL

question_generation:
  batch_size: 4           # Questions per batch
  temperature: 0.3
  max_tokens: 2048
  retry_on_parse_error: 2
  enforce_4_answers: true # Force 4 options (A/B/C/D)

validation:
  min_len: 6              # Min question length (chars)
  max_len: 180            # Max question length (chars)
  banned_words: []
  enable_math_check: true # Verify math calculations
  enable_llm_critique: false
  auto_fix_once: true     # Auto-fix issues once

workflow:
  regen_limit: 2          # Max regeneration attempts
  min_score: 0.0          # Min RAG relevance score
  max_teacher_ctx: 5      # Max teacher context chunks
  max_textbook_ctx: 20    # Max textbook context chunks
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
        "skill_id": "S5"
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
- **hub.py**: Priority-based LLM orchestration với retry, circuit breaker
- **provider_*.py**: Adapter cho từng LLM provider (Ollama, Gemini, etc.)

#### 🔧 Tools (`tools/`)
- **rag_tool.py**: Truy vấn Milvus, rerank, merge context từ SGV + SGK
- **question_generation_tool.py**: Sinh câu hỏi từ context + student profile
- **validation_tool.py**: Rule-based + math checks + optional LLM critique

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
        "accuracy": 0.5,        # Current accuracy (0-1)
        "skill_id": "S5"        # Weak skill
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
            "id": "q1_abc123",
            "text": "3 + 2 = ?",
            "question_type": "multiple_choice",
            "answers": {
                "options": ["3", "4", "5", "6"],
                "correct": 2  # Index of correct answer (0-based)
            },
            "explanation": "3 + 2 = 5",
            "difficulty": 1,
            "provenance": {
                "teacher_ids": ["vec_1", "vec_2"],
                "textbook_ids": ["vec_10"],
                "provider": "gpt_oss_ollama",
                "timestamp": "2025-10-17T10:30:00Z"
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
        }
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
            "question_id": "q1",
            "severity": "critical",
            "message": "Đáp án B và C trùng nhau"
        }
    ],
    "suggested_fixes": [...],
    "applied_fixes": [...],
    "confidence": 0.92
}
```

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
python database/milvus/insert_sgv_to_milvus.py
python database/milvus/insert_sgk_to_milvus.py
```

### 3. Validation Always Fails

**Issue**: Questions keep getting rejected

```yaml
# In configs/agent.yaml, adjust validation:
validation:
  enable_math_check: false  # Disable if too strict
  enable_llm_critique: false
  auto_fix_once: true

workflow:
  regen_limit: 3  # Increase retry limit
```

### 4. Slow Generation

**Issue**: Generation takes > 10 seconds

```yaml
# Optimize config:
rag:
  topk_sgv: 3     # Reduce context size
  topk_sgk: 10

question_generation:
  batch_size: 3   # Generate fewer questions per batch
  max_tokens: 1024  # Reduce token limit

llm:
  timeout_s: 10   # Reduce timeout
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

```python
# Check validation logic in agent/tools/validation_tool.py
# Adjust grade_numeric_range:
validation:
  grade_numeric_range:
    grade1: [0, 100]  # Adjust range for grade
  enable_math_check: true
```

---

## 📚 Tài liệu tham khảo

- [Database README](../database/README.md) - Database setup guide
- [Quiz API README](../backend/quiz_api/README.md) - REST API docs

---

## 🎯 Roadmap

- [ ] Hỗ trợ question types mới: `fill_blank`, `matching`, `ordering`
- [ ] Refine tool với feedback giáo viên
- [ ] A/B testing framework cho prompts
- [ ] Caching layer cho RAG results
- [ ] Multi-language support (English, etc.)
- [ ] Real-time streaming generation

---

**Maintainer**: Mini Adaptive Learning Team  
**Last Updated**: October 17, 2025
