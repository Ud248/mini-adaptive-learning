#!/usr/bin/env python3
"""
Insert SGK to MongoDB - Script nhập dữ liệu SGK vào MongoDB
=========================================================

File này chịu trách nhiệm nhập dữ liệu Sách Giáo Khoa (SGK) vào MongoDB collection.
Chuẩn hóa dữ liệu bài tập và lưu vào textbook_exercises collection.

Chức năng chính:
- Đọc file JSON SGK từ đường dẫn được chỉ định (2 file: tập 1 và tập 2)
- Chuẩn hóa dữ liệu theo quy tắc (loại bỏ difficulty, xử lý null values)
- Nhập dữ liệu vào collection textbook_exercises trong MongoDB

Sử dụng: python database/mongodb/insert_sgk_to_mongodb.py
"""

import json
import os
import sys
from typing import Any, Dict, List
from tqdm import tqdm

# Add project root to path
_CURRENT_DIR = os.path.dirname(__file__)
_PROJECT_ROOT = os.path.abspath(os.path.join(_CURRENT_DIR, '..', '..'))
if _PROJECT_ROOT not in sys.path:
    sys.path.insert(0, _PROJECT_ROOT)

# Import from mongodb_client
from database.mongodb.mongodb_client import (
    connect, insert, create_index, get_collection_info, find_one, update
)

COLLECTION_NAME = "textbook_exercises"

DEFAULT_JSON_1 = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data_insert", "sgk-toan-1-ket-noi-tri-thuc-tap-1.json")
DEFAULT_JSON_2 = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data_insert", "sgk-toan-1-ket-noi-tri-thuc-tap-2.json")


def load_json_file(path: str) -> List[Dict[str, Any]]:
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    if isinstance(data, dict):
        return [data]
    return data


def normalize_item(item: Dict[str, Any]) -> Dict[str, Any]:
    doc = dict(item)

    # drop difficulty if present
    if "difficulty" in doc:
        doc.pop("difficulty", None)

    # normalize answer "null" string to None
    if "answer" in doc and isinstance(doc["answer"], str) and doc["answer"].strip().lower() == "null":
        doc["answer"] = None

    # ensure arrays exist for images
    for k in ["image_question", "image_answer"]:
        if k in doc and doc[k] is None:
            doc[k] = []

    # _id sẽ được set sau khi normalize tất cả items
    doc["metadata"] = {
        "curriculum": "Kết nối tri thức",
        "grade": 1,
        "book_type": "SGK",
    }

    return doc


def main() -> None:
    json1 = os.getenv("SGK_JSON_1", DEFAULT_JSON_1)
    json2 = os.getenv("SGK_JSON_2", DEFAULT_JSON_2)

    items: List[Dict[str, Any]] = []
    for path in [json1, json2]:
        if os.path.exists(path):
            items.extend(load_json_file(path))
        else:
            print(f"⚠️  File not found, skip: {path}")

    normalized: List[Dict[str, Any]] = []
    for it in tqdm(items, desc="Normalizing SGK items", unit="item"):
        try:
            normalized.append(normalize_item(it))
        except Exception as e:
            print(f"❌ Skip item due to error: {e}")

    if not normalized:
        print("No documents to insert.")
        return

    # Override vector_id và _id theo thứ tự tuần tự
    for i, doc in enumerate(normalized):
        doc["vector_id"] = f"vector_{i}"
        doc["_id"] = f"ex_{i}"

    # Kết nối MongoDB
    db = connect()
    
    # Tạo indexes (silent) - bỏ qua lỗi conflict
    try:
        create_index(COLLECTION_NAME, "metadata.curriculum")
        create_index(COLLECTION_NAME, "metadata.grade")
        create_index(COLLECTION_NAME, "metadata.book_type")
        # Bỏ qua vector_id vì có thể đã tồn tại với unique constraint khác
    except Exception:
        pass  # Index có thể đã tồn tại

    # Upsert by _id to avoid duplicates on re-run với progress bar
    inserted = 0
    updated = 0
    for doc in tqdm(normalized, desc="Upserting SGK documents", unit="doc"):
        _id = doc["_id"]  # Không pop _id, giữ lại để tìm kiếm
        # Sử dụng mongodb_client để upsert
        existing = find_one(COLLECTION_NAME, {"_id": _id})
        if existing:
            # Update existing document
            update(COLLECTION_NAME, {"_id": _id}, {"$set": doc})
            updated += 1
        else:
            # Insert new document
            insert(COLLECTION_NAME, doc)
            inserted += 1

    print(f"[SUCCESS] Processed {len(normalized)} docs: {inserted} new, {updated} updated")


if __name__ == "__main__":
    main()


