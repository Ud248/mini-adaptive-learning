
import os
import requests
from pymilvus import Collection
from dotenv import load_dotenv
from pymilvus import MilvusClient
from pymilvus import DataType
load_dotenv('.env')
import milvus_api

# Đọc URL từ biến môi trường hoặc dùng mặc định local
MILVUS_API_URL = os.getenv("MILVUS_URL", "http://localhost:8990")
MILVUS_TOKEN = os.getenv("MILVUS_TOKEN", "http://localhost:8990")
# milvus_client = MilvusClient(uri=MILVUS_API_URL, token=MILVUS_TOKEN)

def send_profile_to_milvus(profile: dict):
    """
    Gửi hồ sơ học sinh gồm:
    - student_id: mã học sinh
    - skills: list[dict]
    - embedding_vector: list[float] (vector biểu diễn năng lực)
    - low_accuracy_skills: list[str]
    - slow_response_skills: list[str]
    """
    try:
        # res = requests.post(f"{MILVUS_API_URL}/insert", json=profile)
        # res.raise_for_status()
        profile_model = milvus_api.StudentProfile(
            student_id=profile["student_id"],
            # embedding_vector=profile.get("embedding_vector", []),
            low_accuracy_skills=profile.get("low_accuracy_skills", []),
            slow_response_skills=profile.get("slow_response_skills", []),
            snapshot=profile.get("snapshot", False)  # optional if included
        )
        milvus_api.insert_profile(profile_model)
        print(f"✅ Đã gửi hồ sơ học sinh {profile.get('student_id')} đến Milvus API")
    except Exception as e:
        print(f"❌ Lỗi khi gửi hồ sơ học sinh {profile.get('student_id')}: {e}")

def get_student_profile(student_id: str):
    """Lấy hồ sơ học sinh từ Milvus"""
    try:
        from pymilvus import Collection, utility
        
        if "profile_student" not in utility.list_collections():
            return None
            
        collection = Collection("profile_student")
        collection.load()
        
        expr = f'student_id == "{student_id}"'
        results = collection.query(
            expr=expr,
            output_fields=["student_id", "low_accuracy_skills", "slow_response_skills", "embedding_vector"]
        )
        
        if not results:
            return None

        r = results[0]
        return {
            "student_id": r["student_id"],
            "low_accuracy_skills": r["low_accuracy_skills"].split(".") if r["low_accuracy_skills"] else [],
            "slow_response_skills": r["slow_response_skills"].split(".") if r["slow_response_skills"] else [],
            "embedding_vector": r["embedding_vector"]
        }
    except Exception as e:
        print(f"Error getting student profile: {e}")
        return None

def get_student_progress_snapshot(student_id: str):
    """Lấy snapshot tiến bộ của học sinh"""
    try:
        from pymilvus import Collection, utility
        
        if "snapshot_student" not in utility.list_collections():
            return []
            
        collection = Collection("snapshot_student")
        collection.load()
        
        expr = f'student_id == "{student_id}"'
        results = collection.query(
            expr=expr,
            output_fields=["id", "timestamp", "low_accuracy_skills", "slow_response_skills", "embedding_vector"]
        )

        results.sort(key=lambda x: x["timestamp"])
        return [
            {
                "id": r["id"],
                "timestamp": r["timestamp"],
                "low_accuracy_skills": r["low_accuracy_skills"].split(".") if r["low_accuracy_skills"] else [],
                "slow_response_skills": r["slow_response_skills"].split(".") if r["slow_response_skills"] else [],
                "embedding_vector": r["embedding_vector"]
            }
            for r in results
        ]
    except Exception as e:
        print(f"Error getting progress snapshot: {e}")
        return []

def get_or_create_skill_progress_collection() -> Collection:
    """Lấy hoặc tạo skill progress collection"""
    try:
        from pymilvus import Collection, utility
        
        collection_name = "skill_progress_collection"
        
        if collection_name not in utility.list_collections():
            print(f"Collection {collection_name} not found")
            return None
            
        collection = Collection(collection_name)
        collection.load()
        return collection
        
    except Exception as e:
        print(f"Error getting skill progress collection: {e}")
        return None