#!/usr/bin/env python3
"""
Insert SGK to Milvus - Script nhập dữ liệu SGK vào Milvus
=========================================================

File này chịu trách nhiệm nhập dữ liệu Sách Giáo Khoa (SGK) vào Milvus collection.
Đọc file JSON SGK, chuẩn hóa dữ liệu, tạo embeddings và lưu vào baitap_collection.

Chức năng chính:
- Đọc file JSON SGK từ đường dẫn được chỉ định (2 file: tập 1 và tập 2)
- Chuẩn hóa dữ liệu theo quy tắc (loại bỏ difficulty, xử lý null values)
- Tạo embeddings 768 chiều từ nội dung bài tập
- Nhập dữ liệu vào collection baitap_collection trong Milvus

Sử dụng: python database/milvus/insert_sgk_to_milvus.py
"""

import json
import os
import sys
import re
from typing import Any, Dict, List, Optional
from tqdm import tqdm

# Ensure project root in path
_CURRENT_DIR = os.path.dirname(__file__)
_PROJECT_ROOT = os.path.abspath(os.path.join(_CURRENT_DIR, '..', '..'))
if _PROJECT_ROOT not in sys.path:
    sys.path.insert(0, _PROJECT_ROOT)

from database.embeddings.local_embedder import LocalEmbedding, EMBEDDING_DIMENSION
from database.milvus.milvus_client import connect, get_collection, insert


MILVUS_ALIAS = "default"
COLLECTION_NAME = "baitap_collection"

DEFAULT_JSON_1 = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data_insert", "sgk-toan-1-ket-noi-tri-thuc-tap-1.json")
DEFAULT_JSON_2 = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data_insert", "sgk-toan-1-ket-noi-tri-thuc-tap-2.json")


def normalize_lesson_text(text: str) -> str:
    """
    Chuẩn hóa text lesson để search tốt hơn
    """
    if not text:
        return ""
    
    # Bước 1: Chuyển về lowercase
    text = text.lower()
    
    # Bước 2: Loại bỏ số tiết trong ngoặc
    text = re.sub(r'\(\s*\d+\s*tiết\s*\)', '', text)
    text = re.sub(r'\(\s*\d+\s*\)', '', text)
    text = re.sub(r'\(\s*tiết\s*\)', '', text)
    text = re.sub(r'\(\s*\d+tiết\s*\)', '', text)  # Không có space
    text = re.sub(r'\(\s*\d+tiết\)', '', text)  # Không có space cuối
    
    # Bước 3: Loại bỏ "Bài X." prefix
    text = re.sub(r'^bài\s+\d+\.\s*', '', text)
    
    # Bước 4: Loại bỏ "Chủ đề X." prefix  
    text = re.sub(r'^chủ đề\s+\d+\.\s*', '', text)
    
    # Bước 5: Loại bỏ dấu câu thừa
    text = re.sub(r'[^\w\s]', ' ', text)
    
    # Bước 6: Chuẩn hóa khoảng trắng
    text = re.sub(r'\s+', ' ', text)
    
    # Bước 7: Loại bỏ từ phụ
    stop_words = ['tiết', 'bài', 'phần', 'chương', 'mục']
    words = text.split()
    words = [word for word in words if word not in stop_words]
    
    return ' '.join(words).strip()


def load_json_file(path: str) -> List[Dict[str, Any]]:
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    if isinstance(data, dict):
        return [data]
    return data


def normalize_item(item: Dict[str, Any]) -> Dict[str, Any]:
    # Copy and clean
    doc = dict(item)
    # remove difficulty
    doc.pop("difficulty", None)
    # fix answer
    if isinstance(doc.get("answer"), str) and doc["answer"].strip().lower() == "null":
        doc["answer"] = None
    return doc


def build_text_for_embedding(doc: Dict[str, Any]) -> str:
    parts: List[str] = []
    if doc.get("question"):
        parts.append(str(doc["question"]))
    if doc.get("lesson"):
        parts.append(str(doc["lesson"]))
    if doc.get("subject"):
        parts.append(str(doc["subject"]))
    if doc.get("source"):
        parts.append(str(doc["source"]))
    return " | ".join(parts)


def connect_milvus() -> None:
    connect()


def main() -> None:
    # Load data
    json1 = os.getenv("SGK_JSON_1", DEFAULT_JSON_1)
    json2 = os.getenv("SGK_JSON_2", DEFAULT_JSON_2)

    items: List[Dict[str, Any]] = []
    for path in [json1, json2]:
        if os.path.exists(path):
            items.extend(load_json_file(path))
        else:
            print(f"⚠️  File not found, skip: {path}")

    if not items:
        print("No input items found.")
        return

    # Normalize
    print("🔄 Normalizing data...")
    docs = [normalize_item(it) for it in tqdm(items, desc="Normalizing items")]

    # Connect Milvus
    print("🔗 Connecting to Milvus...")
    connect_milvus()
    
    # Check collection exists by trying to get it
    try:
        get_collection(COLLECTION_NAME)
    except RuntimeError as e:
        raise RuntimeError(f"Collection '{COLLECTION_NAME}' does not exist. Please create it first.")

    # Prepare embeddings
    print("🧠 Generating embeddings...")
    embedder = LocalEmbedding(verbose=True)
    texts = [build_text_for_embedding(doc) for doc in tqdm(docs, desc="Building texts")]
    embeddings = embedder.embed_texts(texts)

    # Prepare row-wise data for insert function
    print("📝 Preparing data for insertion...")
    insert_data = []
    for i, doc in enumerate(tqdm(docs, desc="Preparing data")):
        vec = embeddings[i] if i < len(embeddings) else [0.0] * EMBEDDING_DIMENSION
        lesson_text = "" if doc.get("lesson") is None else str(doc.get("lesson"))
        normalized_lesson = normalize_lesson_text(lesson_text)
        
        insert_data.append({
            "id": f"vector_{i}",
            "question": "" if doc.get("question") is None else str(doc.get("question")),
            "answer": "" if doc.get("answer") is None else str(doc.get("answer")),
            "lesson": lesson_text,
            "normalized_lesson": normalized_lesson,
            "subject": "" if doc.get("subject") is None else str(doc.get("subject")),
            "source": "" if doc.get("source") is None else str(doc.get("source")),
            "embedding": vec
        })

    # Insert using new milvus_client function
    print("💾 Inserting data into Milvus...")
    insert_result = insert(COLLECTION_NAME, insert_data)
    print(f"✅ Inserted {len(insert_data)} vectors into {COLLECTION_NAME}. Primary keys: {len(insert_result)}")


if __name__ == "__main__":
    main()


