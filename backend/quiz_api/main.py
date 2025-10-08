from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
import random
import json
import os
import uvicorn
from pymongo import MongoClient
from dotenv import load_dotenv
from datetime import datetime, timedelta, timezone
from passlib.context import CryptContext
from jose import jwt, JWTError

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

password_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

_mongo_client: MongoClient | None = None

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
    try:
        return password_context.verify(plain_password, password_hash)
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
    except JWTError:
        return None

def get_current_user(authorization: Optional[str] = None) -> Optional[Dict[str, Any]]:
    if not authorization or not authorization.lower().startswith("bearer "):
        return None
    token = authorization.split(" ", 1)[1]
    payload = decode_token(token)
    if not payload:
        return None
    return {"user_id": payload.get("sub"), "email": payload.get("email"), "role": payload.get("role")}

def load_questions_from_mongo(grade: Optional[int], subject: Optional[str], num_questions: int) -> List[Dict[str, Any]]:
    """Tải câu hỏi từ MongoDB với bộ lọc và random sample."""
    client = get_mongo_client()
    db = client[MONGO_DB_NAME]
    col = db[MONGO_COLLECTION]

    match_stage: Dict[str, Any] = {}
    if grade is not None:
        match_stage["grade"] = grade
    if subject:
        match_stage["subject"] = subject

    pipeline: List[Dict[str, Any]] = []
    if match_stage:
        pipeline.append({"$match": match_stage})
    pipeline.append({"$sample": {"size": max(1, int(num_questions))}})

    docs = list(col.aggregate(pipeline))

    # Fallback nếu sample trả về ít hơn yêu cầu, lấy thêm bằng find (không random)
    if len(docs) < num_questions:
        cursor = col.find(match_stage).limit(num_questions)
        extra = list(cursor)
        # đảm bảo không trùng
        existing_ids = set(str(d.get("_id")) for d in docs)
        for d in extra:
            if str(d.get("_id")) not in existing_ids:
                docs.append(d)
            if len(docs) >= num_questions:
                break

    # Chuẩn hóa sang định dạng Quiz Question
    results: List[Dict[str, Any]] = []
    for q in docs:
        answers = q.get("answers", []) or []
        options = [a.get("text", "") for a in answers]
        correct = ""
        for a in answers:
            if a.get("correct"):
                correct = a.get("text", "")
                break

        image_q = q.get("image_question", "") or ""
        image_a = q.get("image_answer", "") or ""

        results.append({
            "id": q.get("question_id") or str(q.get("_id")),
            "lesson": q.get("skill_name", ""),
            "grade": q.get("grade", 1),
            "chapter": q.get("skill", ""),
            "subject": q.get("subject", ""),
            "source": "mongodb.questions",
            "question": q.get("question", ""),
            "image_question": [image_q] if isinstance(image_q, str) and image_q.strip() else (image_q if isinstance(image_q, list) else []),
            "answer": correct,
            "image_answer": [image_a] if isinstance(image_a, str) and image_a.strip() else (image_a if isinstance(image_a, list) else []),
            "options": options,
            "embedding": [],
            # Lấy giải thích từ 'explaination' (typo phổ biến) hoặc 'explanation'
            "explanation": q.get("explaination") or q.get("explanation") or ""
        })

    return results

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3001", "http://127.0.0.1:3001"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Models
class Question(BaseModel):
    id: str
    lesson: str
    grade: int
    chapter: str
    subject: str
    source: str
    question: str
    image_question: List[str]
    answer: str
    image_answer: List[str]
    options: List[str] = []  # Thêm options cho frontend
    embedding: List[float]
    # Thêm trường giải thích (lấy từ MongoDB key 'explaination' hoặc 'explanation')
    explanation: Optional[str] = None

class QuizRequest(BaseModel):
    grade: Optional[int] = 1  # Mặc định lớp 1
    subject: Optional[str] = "Toán"  # Mặc định môn Toán
    chapter: Optional[str] = None  # Không lọc theo chương
    num_questions: int = 30

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

# Sử dụng dữ liệu từ file grade1_math_questions_complete.json
def load_questions_from_json():
    """Tải câu hỏi từ file grade1_math_questions_complete.json"""
    try:
        # Thử tải từ thư mục gốc
        json_file = '../../grade1_math_questions_complete.json'
        if not os.path.exists(json_file):
            # Nếu không có, thử từ thư mục hiện tại
            json_file = 'grade1_math_questions_complete.json'
        
        with open(json_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # Chuyển đổi cấu trúc dữ liệu từ grade1_math_questions_complete.json
        all_questions = []
        for question_data in data:
            # Tạo ID duy nhất cho câu hỏi
            import hashlib
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
            options = []
            correct_answer = ""
            for answer in question_data.get('answer', []):
                options.append(answer['text'])
                if answer.get('correct'):
                    correct_answer = answer['text']
            
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
        
        print(f"Da tai {len(all_questions)} cau hoi tu {json_file}")
        return all_questions
    except Exception as e:
        print(f"Loi tai du lieu tu JSON: {e}")
        print(f"Chi tiet loi: {type(e).__name__}: {str(e)}")
        print("Dam bao file grade1_math_questions_complete.json ton tai")
        import traceback
        traceback.print_exc()
        return []

def add_image_prefix(image_urls: List[str]) -> List[str]:
    """Thêm tiền tố SeaweedFS vào URL ảnh với format @http://..."""
    base_url = "http://125.212.229.11:8888"
    processed_urls = []
    
    for url in image_urls:
        if not url:  # Bỏ qua URL rỗng
            continue
        elif url.startswith("@"):  # URL đã có format @
            print(f"🖼️ URL đã có format @: {url}")
            processed_urls.append(url)
        elif url.startswith("http"):  # URL đã có protocol, thêm @
            new_url = f"@{url}"
            print(f"🖼️ Thêm @ cho URL: {url} → {new_url}")
            processed_urls.append(new_url)
        elif url.startswith("/"):  # URL bắt đầu với /
            new_url = f"@{base_url}{url}"
            print(f"🖼️ Thêm @ và tiền tố cho URL: {url} → {new_url}")
            processed_urls.append(new_url)
        else:  # URL không có /
            new_url = f"@{base_url}/{url}"
            print(f"🖼️ Thêm @ và tiền tố cho URL: {url} → {new_url}")
            processed_urls.append(new_url)
    
    return processed_urls

@app.get("/")
async def root():
    return {"message": "Quiz System API is running!"}

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

@app.get("/me")
async def me(authorization: Optional[str] = None):
    user = get_current_user(authorization)
    if not user:
        raise HTTPException(status_code=401, detail="Chưa đăng nhập hoặc token không hợp lệ")
    return user

@app.post("/quiz/generate", response_model=QuizResponse)
async def generate_quiz(request: QuizRequest):
    """Tạo bài kiểm tra với số câu hỏi ngẫu nhiên (ưu tiên MongoDB)."""
    try:
        # Thử lấy từ MongoDB
        mongo_questions = load_questions_from_mongo(request.grade, request.subject, request.num_questions)
        selected_questions = mongo_questions

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
            question = Question(
                id=str(q.get("id", random.randint(100000, 999999))),
                lesson=q.get("lesson", ""),
                grade=q.get("grade", 1),
                chapter=q.get("chapter", ""),
                subject=q.get("subject", ""),
                source=q.get("source", ""),
                question=q.get("question", ""),
                image_question=add_image_prefix(q.get("image_question", [])),
                answer=q.get("answer", ""),
                image_answer=add_image_prefix(q.get("image_answer", [])),
                options=q.get("options", []),  # Thêm options
            embedding=q.get("embedding", []),
            explanation=q.get("explanation")
            )
            questions.append(question)
        
        quiz_id = f"quiz_{random.randint(100000, 999999)}"
        
        return QuizResponse(
            quiz_id=quiz_id,
            questions=questions,
            total_questions=len(questions)
        )
        
    except Exception as e:
        print(f"Loi tao bai kiem tra: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Lỗi tạo bài kiểm tra: {str(e)}")

@app.post("/quiz/submit", response_model=QuizResult)
async def submit_quiz(submission: AnswerSubmission):
    """Nop bai va tinh diem"""
    try:
        print(f"Nhan submission: quiz_id={submission.quiz_id}")
        
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
        
        print(f"Tra ve ket qua: score={score}%")
        return result
        
    except Exception as e:
        print(f"Loi xu ly submission: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Loi xu ly bai nop: {str(e)}")

@app.get("/quiz/subjects")
async def get_subjects():
    """Lay danh sach mon hoc"""
    return {
        "subjects": ["Toan", "Tieng Viet", "Khoa hoc", "Lich su", "Dia ly"]
    }

@app.get("/quiz/grades")
async def get_grades():
    """Lay danh sach lop hoc"""
    return {
        "grades": [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12]
    }

@app.get("/quiz/chapters/{subject}")
async def get_chapters(subject: str):
    """Lay danh sach chuong theo mon hoc"""
    chapters = {
        "Toan": ["So hoc", "Hinh hoc", "Dai so", "Thong ke"],
        "Tieng Viet": ["Tu vung", "Ngu phap", "Doc hieu", "Viet"],
        "Khoa hoc": ["Vat ly", "Hoa hoc", "Sinh hoc", "Trai dat"]
    }
    return {"chapters": chapters.get(subject, [])}

@app.post("/quiz/debug-submit")
async def debug_submit(data: dict):
    """Debug endpoint de kiem tra format du lieu"""
    print(f"Debug submission data: {data}")
    print(f"Type of data: {type(data)}")
    print(f"Keys: {data.keys() if isinstance(data, dict) else 'Not a dict'}")
    
    if 'answers' in data:
        print(f"Answers type: {type(data['answers'])}")
        print(f"Answers content: {data['answers']}")
    
    return {
        "message": "Debug data received",
        "received_data": data,
        "data_type": str(type(data))
    }

@app.post("/quiz/submit-simple")
async def submit_quiz_simple(data: dict):
    """Simple submit endpoint without Pydantic models"""
    try:
        quiz_id = data.get("quiz_id", "unknown")
        answers = data.get("answers", {})
        
        total_questions = len(answers)
        correct_answers = min(total_questions, 2)
        score = (correct_answers / total_questions) * 100 if total_questions > 0 else 0
        
        result = {
            "quiz_id": quiz_id,
            "total_questions": total_questions,
            "correct_answers": correct_answers,
            "score": score,
            "message": "Success"
        }
        
        return result
        
    except Exception as e:
        return {"error": "Processing error"}


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8001)
