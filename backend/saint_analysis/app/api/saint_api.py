from fastapi import FastAPI, HTTPException, Path, Query    
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
import traceback
from app.model.simple_updater import update_student_profile, update_student_profile_batch
from app.services.progress_tracker import get_student_progress
from app.database.milvus_client import get_student_profile 
from app.database.milvus_client import get_student_progress_snapshot
from app.database.milvus_client import get_or_create_skill_progress_collection
from app.database.milvus_client import send_profile_to_milvus

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
    student_id: str

class InteractionLog(BaseModel):
    student_id: str
    timestamp: str
    question_text: str
    answer: str
    skill_id: str
    correct: bool
    response_time: float

class InteractionLogs(BaseModel):
    log: list[InteractionLog]

# -------------------- API Endpoint --------------------

@app.post("/analyze")
def analyze_student(query: StudentQuery):
    """Phân tích hồ sơ học sinh"""
    profile = get_student_profile(query.student_id)
    if profile is None:
        raise HTTPException(status_code=404, detail="Không tìm thấy học sinh trong Milvus.")
    return profile

@app.post("/interaction")
def log_interaction(logs: list[InteractionLog]):
    # Ghi log làm bài → cập nhật hồ sơ học sinh với toàn bộ log mới (batch)
    try:
        log_dicts = [log.dict() for log in logs]
        profile = update_student_profile_batch(log_dicts)
        return {
            "status": "Success",
            "profile": profile
        }
    except Exception as e:
        print(67, "---------------------_LOI_----------------------")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/progress/{student_id}")
def get_progress(student_id: str = Path(..., description="ID học sinh")):
    # Trả về lịch sử tiến bộ của học sinh (dựa vào các snapshot đã lưu).
    history = get_student_progress(student_id)
    if not history:
        raise HTTPException(status_code=404, detail="Không tìm thấy lịch sử tiến bộ.")
    return {
        "student_id": student_id,
        "progress_history": history
    }

@app.get("/generate_exercise")
def generate_exercise(student_id: str = Query(..., description="ID học sinh")):
    # Tạo gợi ý bài tập cá nhân hóa dựa trên hồ sơ kỹ năng từ Milvus.
    profile = get_student_profile(student_id)
    if profile is None:
        raise HTTPException(status_code=404, detail="Không tìm thấy học sinh trong Milvus.")

    prompt = (
        f"Bạn là trợ lý giáo viên lớp 1.\n\n"
        f"📉 Kỹ năng yếu của học sinh {student_id}: {', '.join(profile.get('low_accuracy_skills', [])) or 'Không có'}\n"
        f"🐢 Kỹ năng phản hồi chậm: {', '.join(profile.get('slow_response_skills', [])) or 'Không có'}\n\n"
        f"Hãy tạo 5 bài tập đơn giản giúp học sinh luyện các kỹ năng trên."
    )

    suggested_exercises = [
        f"Bài tập {i+1}: [Gợi ý luyện kỹ năng yếu]" for i in range(5)
    ]

    return {
        "student_id": student_id,
        "prompt": prompt,
        "suggested_exercises": suggested_exercises
    }
@app.get("/progress_snapshot/{student_id}")
def get_progress_snapshot(student_id: str):
    snapshots = get_student_progress_snapshot(student_id)
    if not snapshots:
        raise HTTPException(status_code=404, detail="Không tìm thấy snapshot nào.")
    return {
        "student_id": student_id,
        "snapshots": snapshots
    }
@app.get("/skill_trend")
def get_skill_trend(
    student_id: str = Query(..., description="ID học sinh"),
    skill_id: str = Query(..., description="ID kỹ năng")
):
    try:
        collection = get_or_create_skill_progress_collection()
        expr = f'student_id == "{student_id}" and skill_id == "{skill_id}"'
        results = collection.query(
            expr=expr,
            output_fields=["timestamp", "accuracy", "avg_time"]
        )

        # ✅ Ép kiểu float và xử lý timestamp
        progress = []
        for r in results:
            progress.append({
                "timestamp": r["timestamp"],
                "accuracy": float(r["accuracy"]),
                "avg_time": float(r["avg_time"])
            })

        progress.sort(key=lambda x: x["timestamp"])

        return {
            "student_id": student_id,
            "skill_id": skill_id,
            "progress": progress
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Lỗi truy vấn Milvus: {e}")
