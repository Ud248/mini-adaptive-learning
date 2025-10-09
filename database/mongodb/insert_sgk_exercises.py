#!/usr/bin/env python3
"""
Normalize SGK JSON and insert into MongoDB collection `textbook_exercises`.

Rules:
- Remove field `difficulty`.
- If `answer` is string "null", convert to None.
- Keep remaining fields as-is.
- Add `metadata` block: { curriculum: "Kết nối tri thức", grade: 1, book_type: "SGK" }.
- Add `embedding_id`: "vector_<index>".
- _id: "ex_<index>".

Inputs: two JSON files (default paths below). Run from project root.
"""

import json
import os
from typing import Any, Dict, List
from pymongo import MongoClient


MONGODB_URI = os.getenv("MONGODB_URI", "mongodb://localhost:27017")
DB_NAME = "mini_adaptive_learning"
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

    # required fields for ids
    idx = doc.get("index")
    if idx is None:
        raise ValueError("Missing 'index' field in SGK item")

    doc["_id"] = f"ex_{idx}"
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

    print(f"📦 Loaded {len(items)} SGK items")

    normalized: List[Dict[str, Any]] = []
    for it in items:
        try:
            normalized.append(normalize_item(it))
        except Exception as e:
            print(f"❌ Skip item due to error: {e}")

    if not normalized:
        print("No documents to insert.")
        return

    # Override vector_id to sequential order regardless of original index
    for i, doc in enumerate(normalized):
        doc["vector_id"] = f"vector_{i}"

    client = MongoClient(MONGODB_URI)
    db = client[DB_NAME]
    col = db[COLLECTION_NAME]

    # Upsert by _id to avoid duplicates on re-run
    inserted = 0
    for doc in normalized:
        _id = doc.pop("_id")
        res = col.update_one({"_id": _id}, {"$set": doc}, upsert=True)
        if res.upserted_id is not None:
            inserted += 1

    print(f"✅ Upserted {len(normalized)} docs ({inserted} new) into {DB_NAME}.{COLLECTION_NAME}")


if __name__ == "__main__":
    main()


