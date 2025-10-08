"""
MongoDB client for SAINT API - thay thế Milvus cho profile_student
"""

import os
from datetime import datetime, timezone
from pymongo import MongoClient
from dotenv import load_dotenv

load_dotenv()

# MongoDB connection
MONGO_URL = os.getenv("MONGO_URL", "mongodb://localhost:27017")
DATABASE_NAME = os.getenv("DATABASE_NAME", "mini_adaptive_learning")

_mongo_client: MongoClient | None = None

def get_mongo_client() -> MongoClient:
    """Get MongoDB client connection"""
    global _mongo_client
    if _mongo_client is None:
        _mongo_client = MongoClient(MONGO_URL)
        # Test connection
        _mongo_client.admin.command('ping')
    return _mongo_client

def save_student_profile(profile: dict) -> bool:
    """Lưu hoặc cập nhật profile học sinh vào MongoDB (ghi đè hoàn toàn)"""
    try:
        client = get_mongo_client()
        db = client[DATABASE_NAME]
        collection = db["profile_student"]
        
        # Chuẩn bị dữ liệu
        student_email = profile.get("student_email")
        username = profile.get("username", "")
        low_accuracy_skills = profile.get("low_accuracy_skills", [])
        slow_response_skills = profile.get("slow_response_skills", [])
        skills = profile.get("skills", [])
        
        # Tạo document
        profile_doc = {
            "student_email": student_email,
            "username": username,
            "low_accuracy_skills": low_accuracy_skills,
            "slow_response_skills": slow_response_skills,
            "skills": skills,
            "updated_at": datetime.now(timezone.utc),
            "status": "active"
        }
        
        # Kiểm tra xem profile đã tồn tại chưa
        existing = collection.find_one({"student_email": student_email})
        
        if existing:
            # Update existing profile (ghi đè hoàn toàn)
            profile_doc["created_at"] = existing.get("created_at", datetime.now(timezone.utc))
            result = collection.update_one(
                {"student_email": student_email},
                {"$set": profile_doc}
            )
            print(f"✅ Updated student profile (overwritten): {student_email}")
            print(f"   - Low accuracy skills: {low_accuracy_skills}")
            print(f"   - Slow response skills: {slow_response_skills}")
            print(f"   - Total skills tracked: {len(skills)}")
        else:
            # Insert new profile
            profile_doc["created_at"] = datetime.now(timezone.utc)
            result = collection.insert_one(profile_doc)
            print(f"✅ Created new student profile: {student_email}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error saving student profile: {e}")
        return False


def get_student_profile_by_email(email: str) -> dict | None:
    """Lấy profile học sinh theo email"""
    try:
        client = get_mongo_client()
        db = client[DATABASE_NAME]
        collection = db["profile_student"]
        
        profile = collection.find_one({"student_email": email})
        
        if profile:
            profile["_id"] = str(profile["_id"])
            return profile
        else:
            return None
            
    except Exception as e:
        print(f"❌ Error getting student profile by email: {e}")
        return None

def get_student_profile_by_username(username: str) -> dict | None:
    """Lấy profile học sinh theo username"""
    try:
        client = get_mongo_client()
        db = client[DATABASE_NAME]
        collection = db["profile_student"]
        
        profile = collection.find_one({"username": username})
        
        if profile:
            profile["_id"] = str(profile["_id"])
            return profile
        else:
            return None
            
    except Exception as e:
        print(f"❌ Error getting student profile by username: {e}")
        return None

def get_all_student_profiles(limit: int = 100) -> list:
    """Lấy tất cả profiles học sinh"""
    try:
        client = get_mongo_client()
        db = client[DATABASE_NAME]
        collection = db["profile_student"]
        
        profiles = list(collection.find().limit(limit))
        
        # Convert ObjectIds to strings
        for profile in profiles:
            profile["_id"] = str(profile["_id"])
            
        return profiles
        
    except Exception as e:
        print(f"❌ Error getting all student profiles: {e}")
        return []
