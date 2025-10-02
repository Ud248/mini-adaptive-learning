import os
from dotenv import load_dotenv
from pymilvus import Collection
load_dotenv('.env')
import milvus_api

def send_profile_to_milvus(profile: dict):
    try:
        profile_model = milvus_api.StudentProfile(
            student_id=profile["student_id"],
            low_accuracy_skills=profile.get("low_accuracy_skills", []),
            slow_response_skills=profile.get("slow_response_skills", []),
            snapshot=profile.get("snapshot", False)
        )
        milvus_api.insert_profile(profile_model)
        print(f"✅ Đã gửi hồ sơ học sinh {profile.get('student_id')} đến Milvus API")
    except Exception as e:
        print(f"❌ Lỗi khi gửi hồ sơ học sinh {profile.get('student_id')}: {e}")

def get_student_profile(student_id: str):
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



