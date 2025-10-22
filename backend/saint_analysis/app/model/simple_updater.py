"""
Simple updater for SAINT API - tránh lỗi missing dependencies
"""

import json
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

def update_student_profile(log: dict):
    """Simple version - chỉ lưu log và trả về profile cơ bản"""
    student_email = log["student_email"]
    skill_id = log.get("skill_id", "S01")
    correct = log.get("correct", False)
    response_time = log.get("response_time", 5.0)
    
    # Tạo profile đơn giản
    profile = {
        "student_email": student_email,
        "skills": [
            {
                "skill_id": skill_id,
                "accuracy": 0.8 if correct else 0.3,
                "avg_time": response_time,
                "status": "in_progress"
            }
        ],
        "low_accuracy_skills": [skill_id] if not correct else [],
        "slow_response_skills": [skill_id] if response_time > 10 else []
    }
    
    return profile

def update_student_profile_batch(logs: list[dict]):
    """Simple version - xử lý batch logs"""
    if not logs:
        return {"error": "No logs provided"}
    
    student_email = logs[0]["student_email"]
    
    # Lấy username từ log đầu tiên (có thể có hoặc không)
    username = logs[0].get("username", "")
    
    # Tạo profile tổng hợp từ tất cả logs
    all_skills = {}
    low_accuracy = []
    slow_response = []
    
    for log in logs:
        skill_id = log.get("skill_id", "S01")
        correct = log.get("correct", False)
        response_time = log.get("response_time", 0.0)
        # Default to False if missing to avoid mislabeling skipped questions as answered
        is_answered = log.get("is_answered") if "is_answered" in log else False
        
        if skill_id not in all_skills:
            all_skills[skill_id] = {"correct": 0, "total": 0, "times": [], "answered": 0, "skipped": 0}
        
        all_skills[skill_id]["total"] += 1
        
        if is_answered:
            # Câu đã trả lời
            all_skills[skill_id]["answered"] += 1
            all_skills[skill_id]["times"].append(response_time)
            if correct:
                all_skills[skill_id]["correct"] += 1
        else:
            # Câu trống = skill yếu
            all_skills[skill_id]["skipped"] += 1
            all_skills[skill_id]["times"].append(0)  # Thời gian = 0 cho câu trống
            # Câu trống không được tính là correct
    
    # Tính toán kết quả với logic mới
    skills_detail = []
    for skill_id, stats in all_skills.items():
        total_questions = stats["total"]
        answered_questions = stats["answered"]
        skipped_questions = stats["skipped"]
        correct_answers = stats["correct"]
        
        # Accuracy = Số câu đúng / Tổng số câu (bao gồm câu trống)
        accuracy = correct_answers / total_questions if total_questions > 0 else 0
        
        # Thời gian trung bình chỉ tính câu đã trả lời
        answered_times = [t for t in stats["times"] if t > 0]
        avg_time = sum(answered_times) / len(answered_times) if answered_times else 0
        
        # Tính tỷ lệ phần trăm
        answered_rate = answered_questions / total_questions if total_questions > 0 else 0
        skipped_rate = skipped_questions / total_questions if total_questions > 0 else 0
        
        # Xác định trạng thái
        if skipped_questions > 0:
            status = "struggling"  # Có câu trống = struggling
        elif accuracy >= 0.8:
            status = "mastered"
        elif accuracy >= 0.5:
            status = "in_progress"
        else:
            status = "struggling"
        
        skills_detail.append({
            "skill_id": skill_id,
            "accuracy": round(accuracy, 2),
            "avg_time": round(avg_time, 2),
            "answered": round(answered_rate, 2),
            "skipped": round(skipped_rate, 2),
            "status": status
        })
        
        # Xác định skill yếu
        if accuracy < 0.7 or skipped_questions > 0:
            low_accuracy.append(skill_id)
        if avg_time > 10:
            slow_response.append(skill_id)
    
    return {
        "student_email": student_email,
        "username": username,
        "timestamp": datetime.now().isoformat(),
        "skills": skills_detail,
        "low_accuracy_skills": low_accuracy,
        "slow_response_skills": slow_response
    }



