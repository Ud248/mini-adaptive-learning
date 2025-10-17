# 🎯 Quiz API Module

> RESTful API backend cho Mini Adaptive Learning - Quản lý quiz, chấm điểm, authentication và tích hợp với AI Agent

## 📋 Giới thiệu

Module **quiz_api** là backend service chính của hệ thống, đảm nhận:

- 📝 **Quiz Generation**: Tạo bài kiểm tra từ MongoDB hoặc AI Agent
- ✅ **Auto Grading**: Chấm điểm tự động với detailed feedback
- 🔐 **Authentication**: JWT-based auth với MongoDB users
- 👤 **User Management**: Profile, weak skills tracking
- 🤖 **AI Integration**: Tích hợp ALQ-Agent cho adaptive questions
- 📊 **SAINT Integration**: Gửi logs đến knowledge tracing service
- 🖼️ **Image Handling**: SeaweedFS integration cho câu hỏi có hình

## 📑 API Endpoints Quick Reference

### Health Check
- [`GET /`](#1-health-check) - Health check endpoint

### Authentication 🔐
- [`POST /auth/login`](#post-authlogin) - Login với email/username và password
- [`POST /auth/logout`](#post-authlogout) - Logout (stateless)

### Quiz Management 📝
- [`POST /quiz/generate`](#post-quizgenerate) - Tạo bài kiểm tra từ MongoDB (2 câu/skill)
- [`POST /quiz/submit`](#post-quizsubmit) - Nộp bài và chấm điểm tự động

### AI Agent Integration 🤖
- [`POST /agent/questions/generate`](#post-agentquestionsgenerate) - Sinh câu hỏi thông minh bằng AI Agent
- [`POST /agent/questions/validate`](#post-agentquestionsvalidate) - Validate câu hỏi với AI Agent

### User Profile & Skills 👤
- [`GET /api/users/name`](#get-apiusersname) - Lấy thông tin user (cần JWT token)
- [`GET /quiz/weak-skills/{student_email}`](#get-quizweak-skillsstudent_email) - Lấy danh sách kỹ năng yếu
- [`POST /practice/submit`](#post-practicesubmit) - Cập nhật profile sau khi luyện tập

### SAINT Integration 📊
- [`POST /quiz/submit-saint-data`](#post-quizsubmit-saint-data) - Gửi logs đến SAINT service

---

## 🛠️ Tech Stack

```python
# Core
fastapi                 # Web framework
uvicorn                # ASGI server
pydantic               # Data validation

# Database
pymongo                # MongoDB driver
python-dotenv          # Environment variables

# Auth
python-jose[cryptography]  # JWT tokens
passlib                    # Password hashing

# AI Agent
agent.workflow         # Question generation
agent.llm.hub         # Multi-LLM support
```

## � Cài đặt

```bash
# From project root
cd backend/quiz_api

# Install dependencies
pip install -r ../../requirements.txt
```

## ⚙️ Cấu hình

### Environment Variables

Tạo file `.env` ở project root:

```env
# MongoDB
MONGO_URL=mongodb://localhost:27017
DATABASE_NAME=mini_adaptive_learning
QUESTIONS_COLLECTION=placement_questions

# JWT Authentication
JWT_SECRET_KEY=your-secret-change-in-production
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=60

# Image Service (SeaweedFS)
IMAGE_BASE_URL=http://125.212.229.11:8888

# Data Paths (fallback)
SGK_JSON_1=database/data_insert/sgk-toan-1-ket-noi-tri-thuc-tap-1.json
SGK_JSON_2=database/data_insert/sgk-toan-1-ket-noi-tri-thuc-tap-2.json
```

### CORS Settings

API cho phép các origins sau (có thể chỉnh trong `main.py`):

```python
allow_origins=[
    "http://localhost:3000",
    "http://localhost:3001",
    "http://127.0.0.1:3000", 
    "http://127.0.0.1:3001"
]
```

## 🚀 Chạy Server

### Development Mode

```bash
# Method 1: Direct run
cd backend/quiz_api
python main.py

# Method 2: Uvicorn with auto-reload
uvicorn main:app --host 0.0.0.0 --port 8001 --reload

# Method 3: From project root with auto-start script
python app.py  # Starts all services including quiz_api
```

### Production Mode

```bash
# With workers
uvicorn main:app --host 0.0.0.0 --port 8001 --workers 4

# With Gunicorn
gunicorn -w 4 -k uvicorn.workers.UvicornWorker main:app --bind 0.0.0.0:8001
```

Server chạy tại: **`http://localhost:8001`**

Swagger docs: **`http://localhost:8001/docs`**

## 📁 Cấu trúc Module

```
backend/quiz_api/
├── main.py              # 🎯 FastAPI application
│   ├── Routes           # API endpoints
│   ├── Models           # Pydantic schemas
│   ├── Auth             # JWT authentication
│   └── Database         # MongoDB operations
│
├── schemas.py           # 📊 Pydantic models
│   ├── GenerateRequest  # AI agent generation
│   └── ValidateRequest  # Question validation
│
├── README.md            # 📖 This file
└── __pycache__/         # Python cache
```

## 🔌 API Endpoints

### 1. Health Check

#### `GET /`
Health check endpoint

**Response:**
```json
{
  "message": "Quiz System API is running!"
}
```

---

### 2. Authentication 🔐

#### `POST /auth/login`
Login với email/username và password

**Request Body:**
```json
{
  "email_or_username": "student1@gmail.com",
  "password": "password123"
}
```

**Response:**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "expires_in": 3600
}
```

#### `POST /auth/logout`
Logout (stateless - client xóa token)

**Response:**
```json
{
  "message": "Logged out successfully"
}
```

---

### 3. Quiz Management 📝

#### `POST /quiz/generate`
Tạo bài kiểm tra từ MongoDB (2 câu/skill)

**Request Body:**
```json
{
  "grade": 1,
  "subject": "Toán",
  "chapter": null,
  "num_questions": null
}
```

**Response:**
```json
{
  "quiz_id": "quiz_abc123",
  "questions": [
    {
      "id": "Q00001",
      "lesson": "Các số 0, 1, 2, 3, 4, 5",
      "grade": 1,
      "chapter": "S1",
      "subject": "Toán",
      "source": "mongodb.questions",
      "question": "Số nào đứng trước số 3?",
      "image_question": [],
      "answer": "2",
      "image_answer": [],
      "options": ["1", "2", "3", "4"],
      "explanation": "Số đứng trước số 3 là số 2"
    }
  ],
  "total_questions": 12
}
```

#### `POST /quiz/submit`
Nộp bài và chấm điểm tự động

**Request Body:**
```json
{
  "quiz_id": "quiz_abc123",
  "answers": {
    "Q00001": "2",
    "Q00002": "A"
  }
}
```

**Response:**
```json
{
  "quiz_id": "quiz_abc123",
  "total_questions": 12,
  "correct_answers": 10,
  "score": 83.33,
  "detailed_results": [
    {
      "question_id": "Q00001",
      "question_text": "Số nào đứng trước số 3?",
      "user_answer": "2",
      "correct_answer": "2",
      "is_correct": true,
      "explanation": "Số đứng trước số 3 là số 2"
    }
  ],
  "saint_analysis_data": null
}
```

---

### 4. AI Agent Integration 🤖

#### `POST /agent/questions/generate`
Sinh câu hỏi thông minh bằng AI Agent

**Request Body:**
```json
{
  "student_email": "student1@gmail.com",
  "grade": 1,
  "skill": "S5",
  "skill_name": "Mấy và mấy",
  "num_questions": 6
}
```

**Response:**
```json
{
  "questions": [
    {
      "id": "q1_abc123",
      "text": "3 + 2 = ?",
      "question_type": "multiple_choice",
      "answers": {
        "options": ["3", "4", "5", "6"],
        "correct": 2
      },
      "explanation": "3 + 2 = 5",
      "difficulty": 1,
      "provenance": {
        "teacher_ids": ["vec_1"],
        "textbook_ids": ["vec_10"],
        "provider": "gpt_oss_ollama",
        "timestamp": "2025-10-17T10:30:00Z"
      }
    }
  ],
  "metadata": {
    "attempts": 1,
    "timings": {
      "gen_attempt_1": 1200,
      "val_attempt_1": 300
    },
    "validation": {
      "status": "approved",
      "issues": []
    }
  }
}
```

#### `POST /agent/questions/validate`
Validate câu hỏi với AI Agent

**Request Body:**
```json
{
  "questions": [
    {
      "id": "q1",
      "text": "3 + 2 = ?",
      "question_type": "multiple_choice",
      "answers": {
        "options": ["3", "4", "5", "6"],
        "correct": 2
      }
    }
  ],
  "skill": "S5",
  "grade": 1
}
```

**Response:**
```json
{
  "status": "approved",
  "issues": [],
  "confidence": 0.95
}
```

---

### 5. User Profile & Skills 👤

#### `GET /api/users/name`
Lấy thông tin user (cần JWT token)

**Headers:**
```
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

**Response:**
```json
{
  "full_name": "Phan Thiên Ân",
  "username": "student1",
  "email": "student1@gmail.com"
}
```

#### `GET /quiz/weak-skills/{student_email}`
Lấy danh sách kỹ năng yếu của học sinh

**Response:**
```json
{
  "student_email": "student1@gmail.com",
  "profile_data": {
    "total_weak_skills": 3
  },
  "weak_skills": [
    {
      "skill_id": "S5",
      "skill_name": "Mấy và mấy",
      "subject": "Toán",
      "grade": 1,
      "difficulty_level": "medium",
      "status": "struggling",
      "accuracy": 0.45,
      "avg_time": 12.5,
      "answered": 10,
      "skipped": 2,
      "total_questions": 12
    }
  ]
}
```

#### `POST /practice/submit`
Cập nhật profile sau khi luyện tập

**Request Body:**
```json
{
  "student_email": "student1@gmail.com",
  "skill_id": "S5",
  "total_questions": 12,
  "correct_answers": 10,
  "wrong_answers": 2,
  "unanswered_questions": 0,
  "score": 83.33,
  "avg_response_time": 10.5
}
```

**Response:**
```json
{
  "success": true,
  "message": "Profile updated successfully",
  "updated_profile": {
    "skill_id": "S5",
    "accuracy": 0.83,
    "status": "mastered"
  }
}
```

---

### 6. SAINT Integration 📊

#### `POST /quiz/submit-saint-data`
Gửi logs đến SAINT service để phân tích

**Request Body:**
```json
{
  "student_id": "student1",
  "quiz_results": {
    "correct_answers": 10,
    "total_questions": 12
  }
}
```

**Response:**
```json
{
  "success": true,
  "saint_response": { }
}
```

## 🧪 Usage Examples

### 1. Health Check

```bash
curl http://localhost:8001/
```

### 2. Login

```bash
curl -X POST http://localhost:8001/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email_or_username": "student1@gmail.com",
    "password": "123456"
  }'

# Save token
export TOKEN="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
```

### 3. Generate Quiz

```bash
curl -X POST http://localhost:8001/quiz/generate \
  -H "Content-Type: application/json" \
  -d '{
    "grade": 1,
    "subject": "Toán",
    "num_questions": 12
  }'
```

### 4. Submit Quiz

```bash
curl -X POST http://localhost:8001/quiz/submit \
  -H "Content-Type: application/json" \
  -d '{
    "quiz_id": "quiz_abc123",
    "answers": {
      "Q00001": "2",
      "Q00002": "A"
    }
  }'
```

### 5. Get User Info (with JWT)

```bash
curl http://localhost:8001/api/users/name \
  -H "Authorization: Bearer $TOKEN"
```

### 6. Get Weak Skills

```bash
curl http://localhost:8001/quiz/weak-skills/student1@gmail.com
```

### 7. AI Agent Generation

```bash
curl -X POST http://localhost:8001/agent/questions/generate \
  -H "Content-Type: application/json" \
  -d '{
    "student_email": "student1@gmail.com",
    "grade": 1,
    "skill": "S5",
    "skill_name": "Mấy và mấy",
    "num_questions": 6
  }'
```

### 8. Submit Practice Result

```bash
curl -X POST http://localhost:8001/practice/submit \
  -H "Content-Type: application/json" \
  -d '{
    "student_email": "student1@gmail.com",
    "skill_id": "S5",
    "total_questions": 12,
    "correct_answers": 10,
    "wrong_answers": 2,
    "unanswered_questions": 0,
    "score": 83.33,
    "avg_response_time": 10.5
  }'
```

## 🔗 Data Flow

```
Frontend (React)
    ↓
    ├─→ POST /auth/login → JWT Token
    ├─→ GET /api/users/name (with JWT)
    ├─→ GET /quiz/weak-skills/{email}
    ↓
Quiz Flow:
    ├─→ POST /quiz/generate → MongoDB questions
    │   ├─ Fallback: JSON file
    │   └─ 2 questions per skill
    ↓
    ├─→ User answers questions
    ↓
    ├─→ POST /quiz/submit → Auto grading
    │   └─ Detailed results + score
    ↓
    └─→ POST /quiz/submit-saint-data (optional)
        └─ Knowledge tracing analysis

AI Agent Flow:
    ├─→ POST /agent/questions/generate
    │   ├─ RAG Tool → Milvus (SGV/SGK)
    │   ├─ LLM Hub → Ollama/Gemini
    │   ├─ Question Generation Tool
    │   └─ Validation Tool
    ↓
    └─→ Adaptive questions returned
```

## 🔗 Kết nối Module Khác

### Dependencies

```python
# Internal modules
from agent.workflow.agent_workflow import AgentWorkflow
from agent.llm.hub import LLMHub
from agent.tools.validation_tool import ValidationTool
from database.mongodb.mongodb_client import aggregate

# External services
# - MongoDB: Questions, users, profiles, skills
# - Milvus: Vector search (via agent module)
# - SAINT API: Knowledge tracing
# - SeaweedFS: Image storage
```

### Integration Points

1. **Database (MongoDB)**
   - `placement_questions`: Quiz questions
   - `users`: Authentication
   - `profile_student`: Student profiles & weak skills
   - `skills`: Skill metadata

2. **AI Agent Module**
   - `agent/workflow/`: Question generation pipeline
   - `agent/llm/hub`: Multi-LLM orchestration
   - `agent/tools/`: RAG, generation, validation

3. **SAINT Analysis**
   - `backend/saint_analysis/`: Knowledge tracing service
   - POST student interaction logs

4. **Frontend**
   - `frontend/quiz-app/`: React UI
   - Consumes REST APIs

## 🐛 Troubleshooting

### 1. Server Won't Start

**Error**: `Address already in use`

```bash
# Check port 8001
netstat -ano | findstr :8001

# Kill process (Windows)
taskkill /PID <PID> /F

# Or use different port
uvicorn main:app --port 8002
```

### 2. MongoDB Connection Failed

**Error**: `pymongo.errors.ServerSelectionTimeoutError`

```bash
# Check MongoDB is running
docker ps | grep mongo

# Test connection
python -c "
from pymongo import MongoClient
client = MongoClient('mongodb://localhost:27017')
print(client.list_database_names())
"

# Update .env with correct MONGO_URL
```

### 3. Empty Questions

**Issue**: `/quiz/generate` returns empty or too few questions

```bash
# Check MongoDB data
python -c "
from pymongo import MongoClient
client = MongoClient('mongodb://localhost:27017')
db = client['mini_adaptive_learning']
print('Questions count:', db.placement_questions.count_documents({}))
"

# Fallback to JSON
# Make sure file exists:
ls database/data_insert/grade1_math_questions_complete.json
```

### 4. JWT Token Invalid

**Error**: `Invalid token` or `401 Unauthorized`

```bash
# Check JWT_SECRET_KEY in .env
# Token expires after ACCESS_TOKEN_EXPIRE_MINUTES

# Login again to get new token
curl -X POST http://localhost:8001/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email_or_username": "student1@gmail.com", "password": "123456"}'
```

### 5. CORS Errors

**Error**: `Access-Control-Allow-Origin` in browser console

```python
# In main.py, update CORS origins:
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://localhost:3001",
        "http://your-frontend-url"  # Add your URL
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

### 6. AI Agent Generation Failed

**Error**: `LLM_FALLBACK_EXHAUSTED`

```bash
# Check agent module
# 1. Ollama running?
curl http://localhost:11434/api/tags

# 2. Gemini API key?
echo $GEMINI_API_KEY

# 3. Check configs/agent.yaml
cat configs/agent.yaml

# 4. Test agent directly
python -c "
from agent.workflow.agent_workflow import AgentWorkflow
workflow = AgentWorkflow()
print('Agent initialized successfully')
"
```

### 7. Images Not Loading

**Issue**: `image_question` or `image_answer` URLs broken

```bash
# Check SeaweedFS running
curl http://125.212.229.11:8888

# Images should have @ prefix
# Correct: @http://125.212.229.11:8888/path/to/image.png
# API automatically adds prefix in add_image_prefix()
```

### 8. Practice Submit Not Updating Profile

**Issue**: Profile not updating after `/practice/submit`

```bash
# Check if profile exists
python -c "
from pymongo import MongoClient
client = MongoClient('mongodb://localhost:27017')
db = client['mini_adaptive_learning']
profile = db.profile_student.find_one({'student_email': 'student1@gmail.com'})
print(profile)
"

# If null, profile will be created automatically
# Check skills array structure
```

### 9. Swagger Docs Not Working

**Issue**: `/docs` endpoint not loading

```bash
# Make sure server is running
curl http://localhost:8001/

# Access Swagger UI
# http://localhost:8001/docs

# Alternative: ReDoc
# http://localhost:8001/redoc
```

---

## 📚 Tài liệu tham khảo

- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [Pydantic Models](https://docs.pydantic.dev/)
- [JWT Authentication](https://jwt.io/)
- [MongoDB Python Driver](https://pymongo.readthedocs.io/)
- [Agent Module README](../../agent/README.md)
- [Database Module README](../../database/README.md)

---

**Maintainer**: Mini Adaptive Learning Team  
**Last Updated**: October 17, 2025
