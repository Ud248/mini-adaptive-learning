from fastapi import FastAPI, HTTPException, Depends, Header
import sys
import os
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
import random
import json
import uvicorn
from pymongo import MongoClient
from dotenv import load_dotenv
from datetime import datetime, timedelta, timezone
import hashlib
from jose import jwt, JWTError
try:
    from agent.workflow.agent_workflow import AgentWorkflow
    from agent.llm.hub import LLMHub
    from agent.tools.validation_tool import ValidationTool
except ModuleNotFoundError:
    sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))
    from agent.workflow.agent_workflow import AgentWorkflow
    from agent.llm.hub import LLMHub
    from agent.tools.validation_tool import ValidationTool
try:
    from .schemas import GenerateRequest, ValidateRequest
except Exception:
    # Allow running as a script without package context
    sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))
    from backend.quiz_api.schemas import GenerateRequest, ValidateRequest
try:
    from database.mongodb.mongodb_client import aggregate as mongo_aggregate
except ModuleNotFoundError:
    # Add project root to sys.path so 'database' package is importable
    sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))
    from database.mongodb.mongodb_client import aggregate as mongo_aggregate


app = FastAPI(title="Quiz System API", version="1.0.0")

# Load env
load_dotenv()

# MongoDB config
MONGO_URL = os.getenv("MONGO_URL", "mongodb://localhost:27017")
MONGO_DB_NAME = os.getenv("DATABASE_NAME", "mini_adaptive_learning")
MONGO_COLLECTION = os.getenv("QUESTIONS_COLLECTION", "placement_questions")

# Auth config
JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "dev-secret-change-me")
JWT_ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "60"))

_mongo_client: Optional[MongoClient] = None

def get_mongo_client() -> MongoClient:
    global _mongo_client
    if _mongo_client is None:
        _mongo_client = MongoClient(MONGO_URL)
        # warm-up ping
        _mongo_client.admin.command("ping")
    return _mongo_client

# ===================== AUTH MODELS & HELPERS =====================

class LoginRequest(BaseModel):
    email_or_username: str
    password: str

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int


def create_access_token(subject: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
    to_encode = subject.copy()
    expire = datetime.now(timezone.utc) + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)

def verify_password(plain_password: str, password_hash: str) -> bool:
    """Verify password using SHA-256 with salt"""
    try:
        if ':' not in password_hash:
            return False
        salt, stored_hash = password_hash.split(':', 1)
        computed_hash = hashlib.sha256((plain_password + salt).encode('utf-8')).hexdigest()
        return computed_hash == stored_hash
    except Exception:
        return False

def get_user_by_identifier(identifier: str) -> Optional[Dict[str, Any]]:
    client = get_mongo_client()
    db = client[MONGO_DB_NAME]
    col = db["users"]
    user = col.find_one({"email": identifier.lower()})
    if not user:
        user = col.find_one({"username": identifier})
    return user

def decode_token(token: str) -> Optional[Dict[str, Any]]:
    try:
        payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
        return payload
    except JWTError as e:
        return None

def get_current_user(authorization: Optional[str] = Header(None)) -> Optional[Dict[str, Any]]:
    if not authorization or not authorization.lower().startswith("bearer "):
        raise HTTPException(status_code=401, detail="Not authenticated")
    token = authorization.split(" ", 1)[1]
    payload = decode_token(token)
    if not payload:
        raise HTTPException(status_code=401, detail="Invalid token")
    user_data = {"user_id": payload.get("sub"), "email": payload.get("email"), "role": payload.get("role")}
    return user_data

def normalize_questions(docs: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Chuẩn hóa câu hỏi từ MongoDB và resolve skill_id → skill_name, grade, subject."""
    from bson import ObjectId
    
    results: List[Dict[str, Any]] = []
    
    # Get MongoDB collections để resolve references
    client = get_mongo_client()
    db = client[MONGO_DB_NAME]
    skills_col = db["skills"]
    grades_col = db["grades"]
    subjects_col = db["subjects"]
    
    # Cache để tránh query nhiều lần
    skills_cache = {}
    grades_cache = {}
    subjects_cache = {}
    
    for q in docs:
        # Resolve skill_id (ObjectId) → skill info
        skill_id = q.get("skill_id")  # ObjectId reference to skills._id
        skill_name = ""
        grade = 1
        subject = "Toán"
        
        if skill_id:
            # Check cache first
            if skill_id not in skills_cache:
                skill_doc = skills_col.find_one({"_id": skill_id})
                if skill_doc:
                    skills_cache[skill_id] = skill_doc
            
            skill_doc = skills_cache.get(skill_id)
            if skill_doc:
                skill_name = skill_doc.get("skill_name", "")
                
                # Resolve grade_id → grade
                grade_id = skill_doc.get("grade_id")  # ObjectId reference to grades._id
                if grade_id:
                    if grade_id not in grades_cache:
                        grade_doc = grades_col.find_one({"_id": grade_id})
                        if grade_doc:
                            grades_cache[grade_id] = grade_doc.get("grade_name", 1)
                    grade = grades_cache.get(grade_id, 1)
                
                # Resolve subject_id → subject_name
                subject_id = skill_doc.get("subject_id")  # ObjectId reference to subjects._id
                if subject_id:
                    if subject_id not in subjects_cache:
                        subject_doc = subjects_col.find_one({"_id": subject_id})
                        if subject_doc:
                            subjects_cache[subject_id] = subject_doc.get("subject_name", "Toán")
                    subject = subjects_cache.get(subject_id, "Toán")
        
        # Parse answers
        answers = q.get("answers", []) or []
        options = [a.get("text", "") for a in answers]
        correct = ""
        for a in answers:
            if a.get("is_correct"):
                correct = a.get("text", "")
                break

        image_q = q.get("image_question", "") or ""
        image_a = q.get("image_answer", "") or ""

        results.append({
            "id": q.get("question_id") or str(q.get("_id")),
            "lesson": skill_name,  # Resolved từ skill_id
            "skill_name": skill_name,  # Thêm field skill_name cho frontend
            "grade": grade,  # Resolved từ grade_id
            "chapter": skill_name,  # = lesson (để tương thích với frontend)
            "subject": subject,  # Resolved từ subject_id
            "source": "mongodb.placement_questions",
            "question": q.get("question_content") or q.get("question", ""),
            "image_question": [image_q] if isinstance(image_q, str) and image_q.strip() else (image_q if isinstance(image_q, list) else []),
            "answer": correct,
            "image_answer": [image_a] if isinstance(image_a, str) and image_a.strip() else (image_a if isinstance(image_a, list) else []),
            "options": options,
            "embedding": [],
            "explanation": q.get("explaination") or q.get("explanation") or ""
        })

    return results

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://localhost:3001",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:3001"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Models
class Question(BaseModel):
    id: str
    lesson: str
    grade: str
    subject: str
    skill_name: str  # Tên kỹ năng
    question: str
    image_question: List[str]
    answer: str
    image_answer: List[str]
    options: List[str] = []  # Thêm options cho frontend
    explanation: Optional[str] = None  # Giải thích đáp án

class QuizRequest(BaseModel):
    grade: Optional[int] = 1  # Mặc định lớp 1
    subject: Optional[str] = "Toán"  # Mặc định môn Toán
    chapter: Optional[str] = None  # Không lọc theo chương
    num_questions: Optional[int] = None  # Bỏ cố định số câu: mặc định 2 câu/skill

class QuizResponse(BaseModel):
    quiz_id: str
    questions: List[Question]
    total_questions: int

class AnswerSubmission(BaseModel):
    quiz_id: str
    answers: Dict[str, str]  # question_id -> user_answer

class QuizResult(BaseModel):
    quiz_id: str
    total_questions: int
    correct_answers: int
    score: float
    detailed_results: List[Dict[str, Any]]
    saint_analysis_data: Optional[Dict[str, Any]] = None

class PracticeSubmission(BaseModel):
    student_email: str
    skill_id: str
    total_questions: int
    correct_answers: int
    wrong_answers: int
    unanswered_questions: int
    score: float  # percentage (0-100)
    avg_response_time: Optional[float] = None

class PracticeResult(BaseModel):
    success: bool
    message: str
    updated_profile: Optional[Dict[str, Any]] = None

# Sử dụng dữ liệu từ file grade1_math_questions_complete.json
def load_questions_from_json():
    """Tải câu hỏi từ file grade1_math_questions_complete.json"""
    try:
        # Ưu tiên đường dẫn mới trong database/data_insert
        base_dir = os.path.dirname(__file__)
        json_file = os.path.abspath(os.path.join(base_dir, '..', '..', 'database', 'data_insert', 'grade1_math_questions_complete.json'))
        if not os.path.exists(json_file):
            # Fallback: thư mục gốc project (cũ)
            json_file = os.path.abspath(os.path.join(base_dir, '..', '..', 'grade1_math_questions_complete.json'))
        if not os.path.exists(json_file):
            # Fallback: thư mục hiện tại
            json_file = os.path.abspath(os.path.join(base_dir, 'grade1_math_questions_complete.json'))
        
        with open(json_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # Chuyển đổi cấu trúc dữ liệu từ grade1_math_questions_complete.json
        all_questions = []
        for question_data in data:
            # Tạo ID duy nhất cho câu hỏi
            question_text = question_data.get('question', '')
            question_hash = hashlib.md5(question_text.encode()).hexdigest()[:8]
            question_id = f"{question_data.get('skill', 'S1')}_{question_hash}"
            
            # Xử lý image_question
            image_question = []
            if question_data.get('image_question') and question_data['image_question'].strip():
                image_question = [question_data['image_question']]
            
            # Xử lý image_answer
            image_answer = []
            if question_data.get('image_answer') and question_data['image_answer'].strip():
                image_answer = [question_data['image_answer']]
            
            # Tạo options từ answers
            options = [a['text'] for a in question_data.get('answer', [])]
            correct_answer = next((a['text'] for a in question_data.get('answer', []) if a.get('correct')), "")
            
            # Tạo câu hỏi theo format mới
            formatted_question = {
                "id": question_id,
                "lesson": question_data.get('skill_name', ''),
                "grade": question_data.get('grade', 1),
                "chapter": question_data.get('skill', ''),
                "subject": question_data.get('subject', 'Toán'),
                "source": "grade1_math_questions_complete.json",
                "question": question_data.get('question', ''),
                "image_question": image_question,
                "answer": correct_answer,
                "image_answer": image_answer,
                "options": options,
                "embedding": [],  # Không có embedding trong dữ liệu mới
                # Dữ liệu JSON có thể dùng key 'explaination' hoặc 'explanation'
                "explanation": question_data.get('explaination') or question_data.get('explanation') or ""
            }
            all_questions.append(formatted_question)
        
        return all_questions
    except Exception as e:
        return []

def add_image_prefix(image_urls: List[str]) -> List[str]:
    """Thêm tiền tố SeaweedFS vào URL ảnh với format @http://..."""
    base_url = "http://125.212.229.11:8888"
    processed_urls = []
    for url in image_urls:
        if not url:
            continue
        if url.startswith("@"):
            processed_urls.append(url)
            continue
        if url.startswith("http"):
            processed_urls.append(f"@{url}")
            continue
        processed_urls.append(f"@{base_url}{url if url.startswith('/') else '/' + url}")
    return processed_urls

@app.get("/")
async def root():
    return {"message": "Quiz System API is running!"}

@app.get("/quiz/weak-skills/{student_email}")
async def get_weak_skills(student_email: str):
    """Lấy danh sách kỹ năng yếu của học sinh từ profile_student"""
    try:
        from bson import ObjectId
        
        client = get_mongo_client()
        db = client[MONGO_DB_NAME]
        col = db["profile_student"]
        
        # Tìm profile của học sinh
        profile = col.find_one({"student_email": student_email})
        
        if not profile:
            return {"error": "Không tìm thấy profile của học sinh"}
        
        profile_skills = profile.get("skills", []) or profile.get("skill_array", [])

        if profile_skills:
            weak_skill_items = [s for s in profile_skills if str(s.get("status", "")).lower() != "mastered"]

            skills_detail = []
            skills_col = db["skills"]
            grades_col = db["grades"]
            subjects_col = db["subjects"]
            
            for s in weak_skill_items:
                skill_id = s.get("skill_id") or s.get("skill") or ""
                accuracy = s.get("accuracy")
                avg_time = s.get("avg_time") or s.get("avg_response_time") or 0
                status = s.get("status", "unknown")
                answered = s.get("answered", None)
                skipped = s.get("skipped", None)
                total_questions = None
                if isinstance(answered, (int, float)) or isinstance(skipped, (int, float)):
                    total_questions = int((answered or 0) + (skipped or 0))

                # Convert skill_id string to ObjectId if needed
                try:
                    if isinstance(skill_id, str):
                        skill_id = ObjectId(skill_id)
                except:
                    pass
                
                # Enrich từ bảng skills theo skill_id (ObjectId = skills._id)
                skill_info = skills_col.find_one({"_id": skill_id}) or {}
                resolved_skill_name = skill_info.get("skill_name") or s.get("skill_name") or f"{skill_id}"
                
                # Resolve grade_id và subject_id thành tên
                resolved_grade = 1
                resolved_subject = "Toán"
                
                grade_id = skill_info.get("grade_id")
                if grade_id:
                    grade_doc = grades_col.find_one({"_id": grade_id})
                    if grade_doc:
                        resolved_grade = grade_doc.get("grade_name", 1)
                
                subject_id = skill_info.get("subject_id")
                if subject_id:
                    subject_doc = subjects_col.find_one({"_id": subject_id})
                    if subject_doc:
                        resolved_subject = subject_doc.get("subject_name", "Toán")
                
                resolved_difficulty = skill_info.get("difficulty_level") or s.get("difficulty_level") or "medium"

                skills_detail.append({
                    "skill_id": str(skill_id),
                    "skill_name": resolved_skill_name,
                    "subject": resolved_subject,
                    "grade": resolved_grade,
                    "difficulty_level": resolved_difficulty,
                    "status": status,
                    "accuracy": accuracy,
                    "avg_time": avg_time,
                    "answered": answered,
                    "skipped": skipped,
                    "total_questions": total_questions
                })

            return {
                "student_email": student_email,
                "profile_data": {
                    "total_weak_skills": len(skills_detail)
                },
                "weak_skills": skills_detail
            }
        else:
            # Fallback: logic cũ
            low_accuracy_skills = profile.get("low_accuracy_skills", [])
            slow_response_skills = profile.get("slow_response_skills", [])

            skills_col = db["skills"]
            grades_col = db["grades"]
            subjects_col = db["subjects"]
            skills_detail = []
            all_weak_skills = list(set(low_accuracy_skills + slow_response_skills))

            for skill_id in all_weak_skills:
                try:
                    if isinstance(skill_id, str):
                        skill_id = ObjectId(skill_id)
                except:
                    pass
                
                skill_info = skills_col.find_one({"_id": skill_id})
                if skill_info:
                    resolved_grade = 1
                    resolved_subject = "Toán"
                    
                    grade_id = skill_info.get("grade_id")
                    if grade_id:
                        grade_doc = grades_col.find_one({"_id": grade_id})
                        if grade_doc:
                            resolved_grade = grade_doc.get("grade_name", 1)
                    
                    subject_id = skill_info.get("subject_id")
                    if subject_id:
                        subject_doc = subjects_col.find_one({"_id": subject_id})
                        if subject_doc:
                            resolved_subject = subject_doc.get("subject_name", "Toán")
                    
                    skills_detail.append({
                        "skill_id": str(skill_id),
                        "skill_name": skill_info.get("skill_name", f"{skill_id}"),
                        "subject": resolved_subject,
                        "grade": resolved_grade,
                        "difficulty_level": skill_info.get("difficulty_level", "medium"),
                        "status": "unknown"
                    })

            return {
                "student_email": student_email,
                "profile_data": {
                    "low_accuracy_skills": low_accuracy_skills,
                    "slow_response_skills": slow_response_skills,
                    "total_weak_skills": len(all_weak_skills)
                },
                "weak_skills": skills_detail
            }
        
    except Exception as e:
        return {"error": f"Lỗi lấy weak skills: {str(e)}"}

@app.post("/practice/submit", response_model=PracticeResult)
async def submit_practice(submission: PracticeSubmission):
    """
    Update student profile sau khi hoàn thành bài luyện tập skill yếu
    """
    try:
        client = get_mongo_client()
        db = client[MONGO_DB_NAME]
        col = db["profile_student"]
        
        student_email = submission.student_email
        skill_id = submission.skill_id
        
        # Tính toán metrics
        total = submission.total_questions
        correct = submission.correct_answers
        skipped = submission.unanswered_questions
        answered = total - skipped
        
        # Accuracy = score / 100 (convert từ percentage sang [0,1])
        accuracy = submission.score / 100.0
        
        # Xác định status theo logic của simple_updater
        if skipped > 0:
            status = "struggling"  # Có câu trống = struggling
        elif accuracy >= 0.8:
            status = "mastered"
        elif accuracy >= 0.5:
            status = "in_progress"
        else:
            status = "struggling"
        
        # Tìm profile hiện tại
        profile = col.find_one({"student_email": student_email})
        
        if profile:
            # Cập nhật skill trong mảng skills
            skills = profile.get("skills", [])
            
            # Tìm skill cần update
            skill_found = False
            for skill in skills:
                if skill.get("skill_id") == skill_id:
                    # Update skill hiện có
                    skill["accuracy"] = round(accuracy, 2)
                    # avg_time giữ nguyên nếu không có trong submission
                    if submission.avg_response_time is not None:
                        skill["avg_time"] = round(submission.avg_response_time, 2)
                    skill["answered"] = answered
                    skill["skipped"] = skipped
                    skill["status"] = status
                    skill_found = True
                    break
            
            # Nếu chưa có skill này, thêm mới
            if not skill_found:
                skills.append({
                    "skill_id": skill_id,
                    "accuracy": round(accuracy, 2),
                    "avg_time": round(submission.avg_response_time or 0, 2),
                    "answered": answered,
                    "skipped": skipped,
                    "status": status
                })
            
            # Update low_accuracy_skills
            low_accuracy_skills = profile.get("low_accuracy_skills", [])
            
            # Chỉ xử lý skill vừa luyện tập
            # Chỉ xóa khỏi low_accuracy_skills khi:
            # - Accuracy >= 0.8 (mastered)
            # - VÀ không có câu bỏ trống (skipped == 0)
            if accuracy >= 0.8 and skipped == 0:
                # Nếu đạt mastered và làm hết, xóa khỏi low_accuracy_skills
                if skill_id in low_accuracy_skills:
                    low_accuracy_skills.remove(skill_id)
            # Không tự động thêm vào low_accuracy_skills
            # (vì đã được SAINT hoặc logic khác xác định trước đó)
            
            # Cập nhật vào database
            col.update_one(
                {"student_email": student_email},
                {
                    "$set": {
                        "skills": skills,
                        "low_accuracy_skills": low_accuracy_skills,
                        "updated_at": datetime.now(timezone.utc).isoformat()
                    }
                }
            )
        else:
            # Tạo profile mới nếu chưa tồn tại
            new_profile = {
                "student_email": student_email,
                "skills": [{
                    "skill_id": skill_id,
                    "accuracy": round(accuracy, 2),
                    "avg_time": round(submission.avg_response_time or 0, 2),
                    "answered": answered,
                    "skipped": skipped,
                    "status": status
                }],
                "low_accuracy_skills": [],  # Không tự động thêm, để SAINT xác định
                "slow_response_skills": [],
                "created_at": datetime.now(timezone.utc).isoformat(),
                "updated_at": datetime.now(timezone.utc).isoformat()
            }
            col.insert_one(new_profile)
        
        # Lấy profile đã update để trả về
        updated_profile = col.find_one({"student_email": student_email})
        if updated_profile and "_id" in updated_profile:
            updated_profile["_id"] = str(updated_profile["_id"])
        
        return PracticeResult(
            success=True,
            message=f"Đã cập nhật profile cho skill {skill_id}. Status: {status}",
            updated_profile=updated_profile
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Lỗi cập nhật profile: {str(e)}")

@app.post("/auth/login", response_model=TokenResponse)
async def login(req: LoginRequest):
    identifier = (req.email_or_username or "").strip()
    password = req.password or ""
    if not identifier or not password:
        raise HTTPException(status_code=400, detail="Thiếu thông tin đăng nhập")

    user = get_user_by_identifier(identifier)
    if not user or not user.get("password_hash"):
        raise HTTPException(status_code=401, detail="Sai tài khoản hoặc mật khẩu")

    if not verify_password(password, user["password_hash"]):
        raise HTTPException(status_code=401, detail="Sai tài khoản hoặc mật khẩu")

    subject = {
        "sub": str(user.get("_id")),
        "email": user.get("email"),
        "role": user.get("role", "student")
    }
    token = create_access_token(subject)
    return TokenResponse(access_token=token, expires_in=ACCESS_TOKEN_EXPIRE_MINUTES * 60)

@app.post("/auth/logout")
async def logout():
    # Với JWT stateless, logout do client xóa token; server trả 200
    return {"message": "Đăng xuất thành công"}

# ===================== AGENT ENDPOINTS =====================

_hub: Optional[LLMHub] = None
_workflow: Optional[AgentWorkflow] = None
_validator: Optional[ValidationTool] = None


def _get_hub() -> LLMHub:
    global _hub
    if _hub is None:
        # Load full config for LLM providers
        try:
            import yaml  # type: ignore
            path = os.path.join(os.getcwd(), "configs", "agent.yaml")
            cfg = {}
            if os.path.isfile(path):
                with open(path, "r", encoding="utf-8") as f:
                    cfg = yaml.safe_load(f) or {}
        except Exception:
            cfg = {}
        _hub = LLMHub(cfg)
    return _hub


def _get_workflow() -> AgentWorkflow:
    global _workflow
    if _workflow is None:
        _workflow = AgentWorkflow(hub=_get_hub())
    return _workflow


def _get_validator() -> ValidationTool:
    global _validator
    if _validator is None:
        _validator = ValidationTool()
    return _validator


@app.post("/agent/questions:generate")
async def agent_generate(req: GenerateRequest, current_user: dict = Depends(get_current_user)):
    """
    Generate questions using Agent workflow with adaptive student profile
    
    Expected profile_student structure:
    {
        "accuracy": 65,           # % đúng (0-100)
        "answered": 80,           # % đã trả lời (0-100)
        "skipped": 15,            # % bỏ qua (0-100)
        "avg_response_time": 45   # seconds per question
    }
    """
    try:
        wf = _get_workflow()
        
        # Build profile_student with new structure
        # Use values from request, with defaults for backward compatibility
        profile_student = {
            "accuracy": req.accuracy,              # % đúng (0-100)
            "answered": req.answered,              # % đã trả lời (0-100)
            "skipped": req.skipped,                # % bỏ qua (0-100)
            "avg_response_time": req.avg_response_time  # seconds per question
        }
        
        constraints = {
            "grade": req.grade,
            "skill": req.skill,
            "skill_name": req.skill_name or "",
            "num_questions": req.num_questions,
        }
        
        out = wf.run(profile_student=profile_student, constraints=constraints)
        return out
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Agent generate failed: {e}")


@app.post("/agent/questions:validate")
async def agent_validate(req: ValidateRequest, current_user: dict = Depends(get_current_user)):
    try:
        validator = _get_validator()
        report = validator.validate(
            req.questions,
            skill=req.skill,
            teacher_context=req.teacher_context or [],
            textbook_context=req.textbook_context or [],
            grade=req.grade,
        )
        return report
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Agent validate failed: {e}")

 

@app.post("/quiz/generate", response_model=QuizResponse)
async def generate_quiz(request: QuizRequest):
    """Tạo bài kiểm tra: lấy các skill có câu hỏi và mỗi skill 3 câu (1 easy, 1 medium, 1 hard)."""
    try:
        from bson import ObjectId
        
        client = get_mongo_client()
        db = client[MONGO_DB_NAME]
        
        # 1) Resolve grade và subject thành ObjectId
        grade_id = None
        subject_id = None
        
        if request.grade is not None:
            grades_col = db["grades"]
            grade_doc = grades_col.find_one({"grade_name": request.grade})
            if grade_doc:
                grade_id = grade_doc.get("_id")
        
        if request.subject:
            subjects_col = db["subjects"]
            subject_doc = subjects_col.find_one({"subject_name": request.subject})
            if subject_doc:
                subject_id = subject_doc.get("_id")
        
        # 2) Lấy danh sách skill_ids CÓ CÂU HỎI từ placement_questions
        # Filter theo grade_id + subject_id bằng cách join với skills collection
        placement_col = db["placement_questions"]
        skills_col = db["skills"]
        
        # Tìm tất cả skill_ids unique trong placement_questions
        all_skill_ids_in_questions = placement_col.distinct("skill_id")
        
        # Filter những skill_ids này theo grade_id và subject_id
        skills_filter: Dict[str, Any] = {"_id": {"$in": all_skill_ids_in_questions}}
        if subject_id:
            skills_filter["subject_id"] = subject_id
        if grade_id:
            skills_filter["grade_id"] = grade_id
        
        matching_skills = list(skills_col.find(skills_filter, {"_id": 1}))
        available_skill_ids = [s["_id"] for s in matching_skills]
        
        if not available_skill_ids:
            raise HTTPException(status_code=404, detail="Không tìm thấy skill nào có câu hỏi phù hợp")

        # 3) Với mỗi skill_id có câu hỏi: lấy 3 câu (1 easy, 1 medium, 1 hard)
        all_questions_docs: List[Dict[str, Any]] = []
        
        for skill_id in available_skill_ids:
            try:
                # Base match: skill_id trong placement_questions
                base_match = {"skill_id": skill_id}
                
                # Lấy 1 câu easy
                easy_match = base_match.copy()
                easy_match["difficulty"] = "easy"
                easy_docs = mongo_aggregate(MONGO_COLLECTION, [
                    {"$match": easy_match},
                    {"$sample": {"size": 1}}
                ])
                
                # Lấy 1 câu medium
                medium_match = base_match.copy()
                medium_match["difficulty"] = "medium"
                medium_docs = mongo_aggregate(MONGO_COLLECTION, [
                    {"$match": medium_match},
                    {"$sample": {"size": 1}}
                ])
                
                # Lấy 1 câu hard
                hard_match = base_match.copy()
                hard_match["difficulty"] = "hard"
                hard_docs = mongo_aggregate(MONGO_COLLECTION, [
                    {"$match": hard_match},
                    {"$sample": {"size": 1}}
                ])
                
                # Chỉ thêm skill này nếu có đủ 3 câu hỏi (easy, medium, hard)
                if easy_docs and medium_docs and hard_docs:
                    all_questions_docs.extend(easy_docs)
                    all_questions_docs.extend(medium_docs)
                    all_questions_docs.extend(hard_docs)
                else:
                    print(f"⚠️  Skill {skill_id} không đủ 3 độ khó (easy: {len(easy_docs)}, medium: {len(medium_docs)}, hard: {len(hard_docs)})")
                
            except Exception as e:
                print(f"⚠️  Error getting questions for skill_id {skill_id}: {e}")
                continue

        # 4) Chuẩn hóa dữ liệu - resolve skill_id sang skill_name
        selected_questions = normalize_questions(all_questions_docs)

        # Fallback: nếu Mongo không có dữ liệu, thử từ JSON như cũ để dev không bị chặn
        if not selected_questions:
            all_questions = load_questions_from_json()
            if not all_questions:
                raise HTTPException(status_code=404, detail="Không tìm thấy dữ liệu câu hỏi")
            # filter & random như cũ
            filtered_questions = []
            for q in all_questions:
                if request.grade and q.get("grade") != request.grade:
                    continue
                if request.subject and q.get("subject") != request.subject:
                    continue
                filtered_questions.append(q)
            if not filtered_questions:
                filtered_questions = all_questions
            selected_questions = random.sample(
                filtered_questions,
                min(request.num_questions, len(filtered_questions))
            )
        
        # Xử lý dữ liệu
        questions = []
        for q in selected_questions:
            try:
                question = Question(
                    id=str(q.get("id", random.randint(100000, 999999))),
                    lesson=q.get("lesson", ""),
                    grade=q.get("grade", 1),
                    subject=q.get("subject", ""),
                    skill_name=q.get("skill_name", ""),
                    question=q.get("question", ""),
                    image_question=add_image_prefix(q.get("image_question", [])),
                    answer=q.get("answer", ""),
                    image_answer=add_image_prefix(q.get("image_answer", [])),
                    options=q.get("options", []),
                    explanation=q.get("explanation")
                )
                questions.append(question)
            except Exception as e:
                print(f"❌ Error creating Question from data: {e}")
                print(f"   Question data: {q}")
                import traceback
                traceback.print_exc()
                continue
        
        if not questions:
            raise HTTPException(status_code=404, detail="Không thể tạo câu hỏi nào từ dữ liệu")
        
        quiz_id = f"quiz_{random.randint(100000, 999999)}"
        
        return QuizResponse(
            quiz_id=quiz_id,
            questions=questions,
            total_questions=len(questions)
        )
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Error in generate_quiz: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Lỗi tạo bài kiểm tra: {str(e)}")

@app.post("/quiz/submit", response_model=QuizResult)
async def submit_quiz(submission: AnswerSubmission):
    """Nop bai va tinh diem"""
    try:
        
        # Simple calculation
        total_questions = len(submission.answers) if submission.answers else 5
        correct_answers = min(total_questions, 3)  # Simple: assume 3 correct
        score = (correct_answers / total_questions) * 100 if total_questions > 0 else 0
        
        detailed_results = []
        for i, (question_id, user_answer) in enumerate(submission.answers.items()):
            is_correct = i < correct_answers
            detailed_results.append({
                "question_id": question_id,
                "user_answer": user_answer,
                "correct": is_correct,
                "explanation": f"Explanation for question {question_id}"
            })
        
        result = QuizResult(
            quiz_id=submission.quiz_id,
            total_questions=total_questions,
            correct_answers=correct_answers,
            score=score,
            detailed_results=detailed_results,
            saint_analysis_data=None
        )
        
        return result
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Loi xu ly bai nop: {str(e)}")

## Removed: /quiz/subjects (metadata endpoint no longer used by frontend)

## Removed: /quiz/grades (metadata endpoint no longer used by frontend)

## Removed: /quiz/chapters/{subject} (metadata endpoint no longer used by frontend)

@app.post("/quiz/submit-saint-data")
async def submit_saint_data(data: dict):
    """Endpoint riêng để xử lý SAINT data - gửi đến SAINT API thực sự"""
    try:
        logs = data.get("logs", [])
        if not logs:
            return {"message": "No logs to process"}
        
        
        # Gửi đến SAINT API thực sự
        import aiohttp
        async with aiohttp.ClientSession() as session:
            try:
                async with session.post(
                    'http://localhost:8000/interaction',
                    json=logs,
                    timeout=aiohttp.ClientTimeout(total=5)
                ) as response:
                    if response.status == 200:
                        result = await response.json()
                        return {
                            "message": "SAINT data processed successfully",
                            "logs_count": len(logs),
                            "saint_response": result
                        }
                    else:
                        return {"error": f"SAINT API returned {response.status}"}
            except Exception as e:
                return {"error": f"SAINT API call failed: {str(e)}"}
        
    except Exception as e:
        return {"error": "SAINT processing failed"}

# User Profile Management
@app.get("/api/users/name")
async def get_user_name(current_user: dict = Depends(get_current_user)):
    """Get user's full name from MongoDB"""
    try:
        # Get user from MongoDB
        client = get_mongo_client()
        db = client[MONGO_DB_NAME]
        users_collection = db["users"]
        user = users_collection.find_one({"email": current_user["email"]})
        
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        return {
            "full_name": user.get("full_name", ""),
            "username": user.get("username", ""),
            "email": user.get("email", "")
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail="Internal server error")


if __name__ == "__main__":
    uvicorn.run(
        app, 
        host="0.0.0.0", 
        port=8001,
        log_level="info",
        access_log=True,
        reload=False
    )
