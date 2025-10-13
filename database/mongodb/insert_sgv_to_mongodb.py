#!/usr/bin/env python3
"""
Insert SGV to MongoDB - Script nhập dữ liệu SGV vào MongoDB
=========================================================

File này chịu trách nhiệm nhập dữ liệu Sách Giáo Viên (SGV) vào MongoDB collection.
Đọc file JSON SGV, xử lý nội dung và lưu vào teacher_books collection.

Chức năng chính:
- Đọc file JSON SGV từ đường dẫn được chỉ định
- Xử lý và chuẩn hóa nội dung văn bản
- Nhập dữ liệu vào collection teacher_books trong MongoDB

Sử dụng: python database/mongodb/insert_sgv_to_mongodb.py
"""

import json
import os
import sys
from datetime import datetime
from typing import Any, Dict, List
from tqdm import tqdm

# Add project root to path
_CURRENT_DIR = os.path.dirname(__file__)
_PROJECT_ROOT = os.path.abspath(os.path.join(_CURRENT_DIR, '..', '..'))
if _PROJECT_ROOT not in sys.path:
    sys.path.insert(0, _PROJECT_ROOT)

# Import from mongodb_client
from database.mongodb.mongodb_client import (
    connect, insert, create_index, get_collection_info
)

DEFAULT_COLLECTION = "teacher_books"


def get_mongo_client():
    """Kết nối MongoDB sử dụng mongodb_client"""
    return connect()


def ensure_indexes(collection_name: str) -> None:
    """Tạo indexes cho collection"""
    create_index(collection_name, "grade")
    create_index(collection_name, "subject")
    create_index(collection_name, "lesson")
    create_index(collection_name, "metadata.curriculum")
    create_index(collection_name, "metadata.book_type")
    create_index(collection_name, "metadata.year")


def load_json(json_path: str) -> List[Dict[str, Any]]:
    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    if isinstance(data, dict):
        return [data]
    return data


def to_lesson_doc(
    item: Dict[str, Any],
    grade: int,
    subject: str,
    curriculum: str,
    year: int,
    seq_index: int
) -> Dict[str, Any]:
    # lesson title
    raw_lesson = item.get("lesson", "")
    if isinstance(raw_lesson, list):
        lesson_title = " ".join([str(x) for x in raw_lesson])
    else:
        lesson_title = str(raw_lesson)

    # parts
    parts_list = []
    for p in (item.get("parts", []) or []):
        topic = p.get("topic", "")
        content = p.get("content", "")
        parts_list.append({
            "topic": str(topic) if topic is not None else "",
            "content": content if isinstance(content, list) else (str(content) if content is not None else "")
        })

    # info
    infor = item.get("infor", {}) or {}
    page_val = infor.get("page")
    try:
        page = int(page_val) if page_val is not None and str(page_val).isdigit() else None
    except Exception:
        page = None
    source = infor.get("source", "") or ""

    now = datetime.utcnow()

    metadata = {
        "curriculum": curriculum,
        "book_type": "SGV",
        "year": int(year) if year is not None else None,
        "tags": [subject, f"Grade {grade}", curriculum]
    }

    doc: Dict[str, Any] = {
        # Let MongoDB generate _id unless an explicit one is present
        "grade": int(grade),
        "subject": subject,
        "lesson": lesson_title,
        "parts": parts_list,
        "info": {"page": page, "source": source},
        "metadata": metadata,
        "created_at": now,
        "updated_at": now,
    }

    # Vector id aligned with Milvus policy: sequential vector_<index>
    doc["vector_id"] = f"vector_{seq_index}"

    # If source JSON offers an id, preserve it as string _id to avoid collision
    if "id" in item and item["id"] is not None:
        try:
            # Try to coerce to ObjectId if it looks valid
            doc["_id"] = ObjectId(str(item["id"]))
        except Exception:
            doc["_id"] = str(item["id"])  # fallback to string id

    return doc


def main() -> None:
    # Load config from environment or use defaults
    json_path = os.getenv("SGV_JSON_PATH", os.path.join(os.path.dirname(os.path.dirname(__file__)), "data_insert", "sgv_ketnoitrithuc.json"))
    try:
        grade = int(os.getenv("SGV_GRADE", "1"))
    except Exception:
        grade = 1
    subject = os.getenv("SGV_SUBJECT", "Toán")
    try:
        year = int(os.getenv("SGV_YEAR", "2024"))
    except Exception:
        year = 2024
    curriculum = os.getenv("SGV_CURRICULUM", "Kết nối tri thức")

    db = get_mongo_client()
    ensure_indexes(DEFAULT_COLLECTION)

    data = load_json(json_path)
    docs = []
    for i, item in enumerate(tqdm(data, desc="Processing SGV items", unit="item")):
        docs.append(to_lesson_doc(item, grade=grade, subject=subject, curriculum=curriculum, year=year, seq_index=i))

    # Insert many với progress bar
    if not docs:
        print("No documents to insert.")
        return

    result = insert(DEFAULT_COLLECTION, docs, many=True)
    print(f"✅ Inserted {len(result)} documents into {DEFAULT_COLLECTION}")


if __name__ == "__main__":
    main()


