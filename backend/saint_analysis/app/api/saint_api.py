from fastapi import FastAPI, HTTPException, Path, Query    
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
import traceback
from app.model.simple_updater import update_student_profile, update_student_profile_batch
from app.services.progress_tracker import get_student_progress
from app.database.mongodb_client import get_student_profile_by_email, save_student_profile
# from app.database.milvus_client import get_student_progress_snapshot
# from app.database.milvus_client import get_or_create_skill_progress_collection

app = FastAPI(title="SAINT++ API")

# Add CORS middleware first
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# -------------------- Request Schemas --------------------

class StudentQuery(BaseModel):
    student_email: str

class InteractionLog(BaseModel):
    student_email: str
    timestamp: str
    question_text: str
    answer: str
    skill_id: str
    correct: bool
    response_time: float
    is_answered: bool | None = None

class InteractionLogs(BaseModel):
    log: list[InteractionLog]

# -------------------- API Endpoint --------------------

@app.post("/analyze")
def analyze_student(query: StudentQuery):
    """Phân tích hồ sơ học sinh"""
    profile = get_student_profile_by_email(query.student_email)
    if profile is None:
        raise HTTPException(status_code=404, detail="Không tìm thấy học sinh trong MongoDB.")
    return profile

@app.post("/interaction")
def log_interaction(logs: list[InteractionLog]):
    # Ghi log làm bài → cập nhật hồ sơ học sinh với toàn bộ log mới (batch)
    try:
        # Ensure backward compatibility: if is_answered is missing, infer from answer
        log_dicts = []
        for log in logs:
            d = log.dict()
            if d.get("is_answered") is None:
                # Consider empty string or None as not answered
                ans = d.get("answer")
                d["is_answered"] = bool(ans) and str(ans).strip() != ""
            log_dicts.append(d)
        profile = update_student_profile_batch(log_dicts)

        # Debug: summarize answered/skipped per skill before saving
        try:
            skills = profile.get("skills", [])
            print("[SAINT] Profile summary before save → skills:")
            for s in skills:
                print(
                    f"  - skill_id={s.get('skill_id')} answered={s.get('answered')} skipped={s.get('skipped')} accuracy={s.get('accuracy')} avg_time={s.get('avg_time')} status={s.get('status')}"
                )
        except Exception:
            pass
        
        # Lưu profile vào MongoDB
        save_student_profile(profile)
        
        return {
            "status": "Success",
            "profile": profile
        }
    except Exception as e:
        print(67, "---------------------_LOI_----------------------")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/progress/{student_email}")
def get_progress(student_email: str = Path(..., description="Email học sinh")):
    # Trả về lịch sử tiến bộ của học sinh (dựa vào các snapshot đã lưu).
    history = get_student_progress(student_email)
    if not history:
        raise HTTPException(status_code=404, detail="Không tìm thấy lịch sử tiến bộ.")
    return {
        "student_email": student_email,
        "progress_history": history
    }

@app.get("/generate_exercise")
def generate_exercise(student_email: str = Query(..., description="Email học sinh")):
    # Tạo gợi ý bài tập cá nhân hóa dựa trên hồ sơ kỹ năng từ MongoDB.
    profile = get_student_profile_by_email(student_email)
    if profile is None:
        raise HTTPException(status_code=404, detail="Không tìm thấy học sinh trong MongoDB.")

    prompt = (
        f"Bạn là trợ lý giáo viên lớp 1.\n\n"
        f"📉 Kỹ năng yếu của học sinh {student_email}: {', '.join(profile.get('low_accuracy_skills', [])) or 'Không có'}\n"
        f"🐢 Kỹ năng phản hồi chậm: {', '.join(profile.get('slow_response_skills', [])) or 'Không có'}\n\n"
        f"Hãy tạo 5 bài tập đơn giản giúp học sinh luyện các kỹ năng trên."
    )

    suggested_exercises = [
        f"Bài tập {i+1}: [Gợi ý luyện kỹ năng yếu]" for i in range(5)
    ]

    return {
        "student_email": student_email,
        "prompt": prompt,
        "suggested_exercises": suggested_exercises
    }
@app.get("/progress_snapshot/{student_email}")
def get_progress_snapshot(student_email: str):
    # Tạm thời disable Milvus functionality
    return {
        "student_email": student_email,
        "snapshots": [],
        "message": "Milvus functionality temporarily disabled"
    }
@app.get("/skill_trend")
def get_skill_trend(
    student_email: str = Query(..., description="Email học sinh"),
    skill_id: str = Query(..., description="ID kỹ năng")
):
    # Tạm thời disable Milvus functionality
    return {
        "student_email": student_email,
        "skill_id": skill_id,
        "progress": [],
        "message": "Milvus functionality temporarily disabled"
    }
