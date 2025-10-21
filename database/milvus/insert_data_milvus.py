#!/usr/bin/env python3
"""
Insert Data to Milvus - Script nhập dữ liệu từ MongoDB vào Milvus
==================================================================

File này chịu trách nhiệm nhập dữ liệu từ MongoDB vào Milvus collections:
- baitap_collection: Dữ liệu từ textbook_exercises collection
- sgv_collection: Dữ liệu từ teacher_books collection

Chức năng chính:
- Lấy dữ liệu từ MongoDB (textbook_exercises, teacher_books, skills)
- Tạo embeddings 768 chiều từ nội dung
- Nhập dữ liệu vào Milvus collections

Sử dụng: python database/milvus/insert_data_milvus.py
"""

import os
import sys
import traceback
from typing import Any, Dict, List
from tqdm import tqdm

# Ensure project root in path
_CURRENT_DIR = os.path.dirname(__file__)
_PROJECT_ROOT = os.path.abspath(os.path.join(_CURRENT_DIR, '..', '..'))
if _PROJECT_ROOT not in sys.path:
    sys.path.insert(0, _PROJECT_ROOT)

from database.embeddings.local_embedder import LocalEmbedding, EMBEDDING_DIMENSION
from database.milvus.milvus_client import connect, get_collection, insert
from database.mongodb.mongodb_client import get_collection as get_mongodb_collection
from pymilvus import Collection
from bson import ObjectId

# Constants
SGK_COLLECTION_NAME = "baitap_collection"
SGV_COLLECTION_NAME = "sgv_collection"


# ============================================================================
# SHARED FUNCTIONS
# ============================================================================

def connect_milvus() -> None:
    """Kết nối đến Milvus"""
    connect()


def get_skill_name_from_id(skill_id: str) -> str:
    """Lấy tên skill từ skill_id (ObjectId) trong MongoDB"""
    try:
        if not skill_id:
            return ""
        
        skills_collection = get_mongodb_collection("skills")
        
        # Convert string skill_id thành ObjectId
        try:
            object_id = ObjectId(skill_id)
            skill_doc = skills_collection.find_one({"_id": object_id})
            if skill_doc:
                return skill_doc.get("skill_name", "")
        except Exception:
            # Nếu không convert được ObjectId, trả về rỗng
            pass
        
        return ""
    except Exception as e:
        print(f"⚠️  Error getting skill name for {skill_id}: {e}")
        return ""


# ============================================================================
# BAITAP COLLECTION (Textbook Exercises from MongoDB) FUNCTIONS
# ============================================================================

def build_baitap_text_for_embedding(exercise: Dict[str, Any]) -> str:
    """Xây dựng text cho embedding từ textbook exercise"""
    parts: List[str] = []
    if exercise.get("question_content"):
        parts.append(str(exercise["question_content"]))
    if exercise.get("lesson"):
        parts.append(str(exercise["lesson"]))
    if exercise.get("source"):
        parts.append(str(exercise["source"]))
    return " | ".join(parts)


def insert_baitap_data() -> None:
    """Nhập dữ liệu bài tập từ MongoDB vào Milvus"""
    print("\n" + "="*60)
    print("📚 INSERTING BAITAP DATA (from MongoDB)")
    print("="*60)
    
    # Connect Milvus
    print("🔗 Connecting to Milvus...")
    connect_milvus()
    
    # Check collection exists
    try:
        collection = get_collection(SGK_COLLECTION_NAME)
        print(f"✅ Collection '{SGK_COLLECTION_NAME}' exists")
    except RuntimeError as e:
        raise RuntimeError(f"Collection '{SGK_COLLECTION_NAME}' does not exist. Please run setup_milvus.py first.")

    # Clear existing data
    print(f"🗑️  Clearing existing data from '{SGK_COLLECTION_NAME}'...")
    try:
        collection.delete(expr="id != ''")  # Delete all records
        print(f"✅ Cleared data from '{SGK_COLLECTION_NAME}'")
    except Exception as e:
        print(f"⚠️  Warning while clearing data: {e}")
    
    # Load data from MongoDB
    print("📖 Loading data from MongoDB (textbook_exercises collection)...")
    try:
        exercises_collection = get_mongodb_collection("textbook_exercises")
        
        exercises = list(exercises_collection.find())
        if not exercises:
            print("❌ No exercises found in MongoDB.")
            return
        
        print(f"✅ Loaded {len(exercises)} exercises from MongoDB")
    except Exception as e:
        raise RuntimeError(f"Failed to load data from MongoDB: {e}")

    # Prepare embeddings
    print("🧠 Generating embeddings...")
    embedder = LocalEmbedding(verbose=True)
    texts = [build_baitap_text_for_embedding(ex) for ex in tqdm(exercises, desc="Building texts")]
    embeddings = embedder.embed_texts(texts)

    # Prepare data for insert
    print("📝 Preparing data for insertion...")
    insert_data = []
    
    for i, exercise in enumerate(tqdm(exercises, desc="Preparing data")):
        vec = embeddings[i] if i < len(embeddings) else [0.0] * EMBEDDING_DIMENSION
        
        # Get skill_name from skill_id
        skill_id = exercise.get("skill_id", "")
        skill_name = get_skill_name_from_id(skill_id) if skill_id else ""
        
        insert_data.append({
            "id": str(exercise.get("vector_id", f"baitap_{i}")),
            "question_content": "" if exercise.get("question_content") is None else str(exercise.get("question_content")),
            "lesson": "" if exercise.get("lesson") is None else str(exercise.get("lesson")),
            "skill_name": skill_name,
            "source": "" if exercise.get("source") is None else str(exercise.get("source")),
            "embedding": vec
        })

    # Insert
    print("💾 Inserting data into Milvus...")
    insert_result = insert(SGK_COLLECTION_NAME, insert_data)
    print(f"✅ Inserted {len(insert_data)} vectors into '{SGK_COLLECTION_NAME}'. Primary keys: {len(insert_result)}")


# ============================================================================
# SGV COLLECTION (Teacher Books from MongoDB) FUNCTIONS
# ============================================================================

def build_sgv_text_for_embedding(teacher_book: Dict[str, Any]) -> str:
    """Xây dựng text cho embedding từ teacher book - chỉ lấy 2 part đầu tiên"""
    parts: List[str] = []
    
    # Duyệt chỉ 2 part đầu tiên
    book_parts = teacher_book.get("parts", []) or []
    for idx, part in enumerate(book_parts):
        if idx >= 2:  # Chỉ lấy 2 part đầu tiên (idx 0 và 1)
            break
        
        if isinstance(part, dict):
            topic = part.get("topic", "")
            content = part.get("content", "")
            
            if topic:
                parts.append(str(topic))
            if content:
                parts.append(str(content))
    
    return " | ".join(parts)


def build_sgv_content(teacher_book: Dict[str, Any]) -> str:
    """Xây dựng content từ parts array"""
    content_parts: List[str] = []
    
    book_parts = teacher_book.get("parts", []) or []
    for part in book_parts:
        if isinstance(part, dict):
            topic = part.get("topic", "")
            content = part.get("content", "")
            
            if topic:
                content_parts.append(str(topic))
            if content:
                if isinstance(content, list):
                    content_parts.extend([str(c) for c in content])
                else:
                    content_parts.append(str(content))
    
    return "\n".join(content_parts)


def insert_sgv_data() -> None:
    """Nhập dữ liệu SGV từ MongoDB vào Milvus"""
    print("\n" + "="*60)
    print("📖 INSERTING SGV DATA (from MongoDB)")
    print("="*60)

    # Connect Milvus
    print("🔗 Connecting to Milvus...")
    connect_milvus()

    # Check collection exists
    try:
        collection = get_collection(SGV_COLLECTION_NAME)
        print(f"✅ Collection '{SGV_COLLECTION_NAME}' exists")
    except RuntimeError as e:
        raise RuntimeError(f"Collection '{SGV_COLLECTION_NAME}' does not exist. Please run setup_milvus.py first.")

    # Clear existing data
    print(f"🗑️  Clearing existing data from '{SGV_COLLECTION_NAME}'...")
    try:
        collection.delete(expr="id != ''")  # Delete all records
        print(f"✅ Cleared data from '{SGV_COLLECTION_NAME}'")
    except Exception as e:
        print(f"⚠️  Warning while clearing data: {e}")

    # Load data from MongoDB
    print("📖 Loading data from MongoDB (teacher_books collection)...")
    try:
        teacher_books_collection = get_mongodb_collection("teacher_books")
        
        teacher_books = list(teacher_books_collection.find())
        if not teacher_books:
            print("❌ No teacher books found in MongoDB.")
            return
        
        print(f"✅ Loaded {len(teacher_books)} teacher books from MongoDB")
    except Exception as e:
        raise RuntimeError(f"Failed to load data from MongoDB: {e}")

    # Generate embeddings
    print("🧠 Generating embeddings...")
    embedder = LocalEmbedding(verbose=True)
    texts = [build_sgv_text_for_embedding(book) for book in tqdm(teacher_books, desc="Building texts")]
    embeddings = embedder.embed_texts(texts)

    if not embeddings or any(len(vec) != EMBEDDING_DIMENSION for vec in embeddings):
        raise ValueError("Embedding generation failed or wrong dimension")

    # Prepare data for insert
    print("📝 Preparing data for insertion...")
    insert_data = []
    
    for i, (teacher_book, embedding) in enumerate(tqdm(zip(teacher_books, embeddings), desc="Preparing data", total=len(teacher_books))):
        # Get skill_name from skill_id
        skill_id = teacher_book.get("skill_id", "")
        skill_name = get_skill_name_from_id(skill_id) if skill_id else ""
        
        # Get source from info/source
        info = teacher_book.get("info", {}) or {}
        source = info.get("source", "")
        
        insert_data.append({
            "id": str(teacher_book.get("vector_id", f"sgv_{i}")),
            "lesson": "" if teacher_book.get("lesson") is None else str(teacher_book.get("lesson")),
            "skill_name": skill_name,
            "content": build_sgv_content(teacher_book),
            "source": "" if source is None else str(source),
            "embedding": embedding
        })

    # Insert
    print("💾 Inserting data into Milvus...")
    insert_result = insert(SGV_COLLECTION_NAME, insert_data)
    print(f"✅ Inserted {len(insert_data)} rows into '{SGV_COLLECTION_NAME}'. Primary keys: {len(insert_result)}")


# ============================================================================
# MAIN FUNCTION
# ============================================================================

def main():
    """Chạy insert dữ liệu bài tập và sách giáo viên vào Milvus"""
    try:
        insert_baitap_data()
        insert_sgv_data()

        print("\n" + "="*60)
        print("🎉 Data insertion completed successfully!")
        print("="*60)

    except Exception as e:
        print(f"\n❌ Insert failed: {e}")
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
