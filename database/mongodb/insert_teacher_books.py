#!/usr/bin/env python3
"""
Create MongoDB collection `teacher_books` and insert SGV data.

Schema (per document = one lesson):
{
  _id: string|ObjectId,
  grade: int,
  subject: string,
  lesson: string,
  parts: [ { topic: string, content: string|[string] } ],
  info: { page: int, source: string },
  metadata: { curriculum: string, book_type: "SGV", year: int, tags: [string] },
  created_at: datetime,
  updated_at: datetime
}

Usage:
  # From project root (no arguments needed)
  python database/mongodb/insert_teacher_books.py

Environment variables (optional overrides):
  MONGODB_URI: connection string (default: mongodb://localhost:27017)
  SGV_JSON_PATH: path to json (default: absolute path to database/data_insert/sgv_ketnoitrithuc.json)
  SGV_GRADE: grade number (default: 1)
  SGV_SUBJECT: subject name (default: "Toán")
  SGV_YEAR: publication year (default: 2024)
  SGV_CURRICULUM: curriculum name (default: "Kết nối tri thức")
"""

import json
import os
from datetime import datetime
from typing import Any, Dict, List

from pymongo import MongoClient
from bson import ObjectId


DEFAULT_DB_NAME = "mini_adaptive_learning"
DEFAULT_COLLECTION = "teacher_books"


def get_mongo_client() -> MongoClient:
    uri = os.getenv("MONGODB_URI", "mongodb://localhost:27017")
    return MongoClient(uri)


def ensure_indexes(collection) -> None:
    """No-op: Indexes are created in setup_mongodb.py"""
    return None


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

    client = get_mongo_client()
    db = client[DEFAULT_DB_NAME]
    col = db[DEFAULT_COLLECTION]

    ensure_indexes(col)

    data = load_json(json_path)
    docs = []
    for i, item in enumerate(data):
        docs.append(to_lesson_doc(item, grade=grade, subject=subject, curriculum=curriculum, year=year, seq_index=i))

    # Insert many
    if not docs:
        print("No documents to insert.")
        return

    result = col.insert_many(docs)
    print(f"Inserted {len(result.inserted_ids)} documents into {DEFAULT_DB_NAME}.{DEFAULT_COLLECTION}")


if __name__ == "__main__":
    main()


