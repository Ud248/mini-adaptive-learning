"""
Simple updater for SAINT API - tránh lỗi missing dependencies
"""

import json
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

def update_student_profile(log: dict):
    """Simple version - chỉ lưu log và trả về profile cơ bản"""
    student_id = log["student_id"]
    skill_id = log.get("skill_id", "S01")
    correct = log.get("correct", False)
    response_time = log.get("response_time", 5.0)
    
    # Tạo profile đơn giản
    profile = {
        "student_id": student_id,
        "skills": [
            {
                "skill_id": skill_id,
                "skill_name": f"Skill {skill_id}",
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
    
    student_id = logs[0]["student_id"]
    
    # Tạo profile tổng hợp từ tất cả logs
    all_skills = {}
    low_accuracy = []
    slow_response = []
    
    for log in logs:
        skill_id = log.get("skill_id", "S01")
        correct = log.get("correct", False)
        response_time = log.get("response_time", 5.0)
        
        if skill_id not in all_skills:
            all_skills[skill_id] = {"correct": 0, "total": 0, "times": []}
        
        all_skills[skill_id]["total"] += 1
        all_skills[skill_id]["times"].append(response_time)
        if correct:
            all_skills[skill_id]["correct"] += 1
    
    # Tính toán kết quả
    skills_detail = []
    for skill_id, stats in all_skills.items():
        accuracy = stats["correct"] / stats["total"] if stats["total"] > 0 else 0
        avg_time = sum(stats["times"]) / len(stats["times"])
        
        skills_detail.append({
            "skill_id": skill_id,
            "skill_name": f"Skill {skill_id}",
            "accuracy": round(accuracy, 2),
            "avg_time": round(avg_time, 2),
            "status": "mastered" if accuracy > 0.8 else "in_progress" if accuracy > 0.5 else "struggling"
        })
        
        if accuracy < 0.7:
            low_accuracy.append(skill_id)
        if avg_time > 10:
            slow_response.append(skill_id)
    
    return {
        "student_id": student_id,
        "timestamp": datetime.now().isoformat(),
        "skills": skills_detail,
        "low_accuracy_skills": low_accuracy,
        "slow_response_skills": slow_response
    }



