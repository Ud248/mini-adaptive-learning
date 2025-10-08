import os
from dotenv import load_dotenv

from pymilvus import Collection, utility, connections
load_dotenv('.env')

def _ensure_connected():
    """Đảm bảo kết nối Milvus đã được thiết lập."""
    host = os.getenv("MILVUS_HOST", os.getenv("MILVUS_URL", "localhost"))
    port = os.getenv("MILVUS_PORT", "19530")
    try:
        if ":" in host and host.count(":") == 1:
            host_part, port_part = host.split(":")
            if port_part.isdigit():
                host, port = host_part, port_part
        connections.connect(alias="default", host=host, port=port)
    except Exception as e:
        print(f"[milvus_client.db] Kết nối Milvus lỗi ({host}:{port}): {e}")



def get_student_progress_snapshot(student_email: str):
    try:
        _ensure_connected()
        if "snapshot_student" not in utility.list_collections():
            return []
        collection = Collection("snapshot_student")
        collection.load()
        expr = f'student_id == "{student_email}"'
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
        _ensure_connected()
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



