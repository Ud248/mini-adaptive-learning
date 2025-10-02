import os
import json
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

# Đường dẫn file lưu lịch sử tiến bộ
DATA_DIR = os.getenv("DATA_DIR", "data/saintpp_data")
PROGRESS_FILE = os.path.join(DATA_DIR, "interactions", "student_progress.jsonl")

def save_progress_snapshot(profile: dict):
    """
    Ghi lại snapshot tiến bộ của học sinh vào file JSON Lines.
    Mỗi dòng là một bản ghi: student_id, timestamp, kỹ năng, embedding.
    """
    snapshot = {
        "student_id": profile["student_id"],
        "timestamp": datetime.now().isoformat(),
        "low_accuracy_skills": profile.get("low_accuracy_skills", []),
        "slow_response_skills": profile.get("slow_response_skills", []),
        "embedding_vector": profile.get("embedding_vector", [])
    }

    os.makedirs(os.path.dirname(PROGRESS_FILE), exist_ok=True)
    with open(PROGRESS_FILE, "a", encoding="utf-8") as f:
        f.write(json.dumps(snapshot, ensure_ascii=False) + "\n")

    print(f"📊 Đã ghi snapshot tiến bộ cho học sinh {profile['student_id']}.")

def get_student_progress(student_id: str) -> list[dict]:
    """
    Trả về danh sách các mốc tiến bộ của học sinh theo thời gian.
    """
    if not os.path.exists(PROGRESS_FILE):
        return []

    progress = []
    with open(PROGRESS_FILE, "r", encoding="utf-8") as f:
        for line in f:
            try:
                record = json.loads(line)
                if record.get("student_id") == student_id:
                    progress.append(record)
            except Exception:
                continue

    # Sắp xếp theo thời gian tăng dần
    progress.sort(key=lambda x: x.get("timestamp", ""))
    return progress
