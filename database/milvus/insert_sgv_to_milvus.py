#!/usr/bin/env python3
"""
Insert SGV to Milvus - Script nhập dữ liệu SGV vào Milvus
=========================================================

File này chịu trách nhiệm nhập dữ liệu Sách Giáo Viên (SGV) vào Milvus collection.
Đọc file JSON SGV, xử lý nội dung, tạo embeddings và lưu vào sgv_collection.

Chức năng chính:
- Đọc file JSON SGV từ đường dẫn được chỉ định
- Xử lý và làm sạch nội dung văn bản (sửa lỗi OCR, chuẩn hóa)
- Tạo embeddings 768 chiều bằng Vietnamese sentence-transformer
- Nhập dữ liệu vào collection sgv_collection trong Milvus

Sử dụng: python database/milvus/insert_sgv_to_milvus.py
"""

import json
import os
import sys
import re
import traceback
from typing import List, Dict, Any
from tqdm import tqdm

# Ensure project root is on sys.path when running as a script
_CURRENT_DIR = os.path.dirname(__file__)
_PROJECT_ROOT = os.path.abspath(os.path.join(_CURRENT_DIR, '..', '..'))
if _PROJECT_ROOT not in sys.path:
    sys.path.insert(0, _PROJECT_ROOT)

# Local modules (absolute import from project root)
from database.embeddings.local_embedder import LocalEmbedding, EMBEDDING_DIMENSION
from database.milvus.milvus_client import connect, get_collection, insert


MILVUS_ALIAS = "default"
COLLECTION_NAME = "sgv_collection"
DEFAULT_JSON_PATH = os.path.join(
    os.path.dirname(os.path.dirname(__file__)),  # database/
    "data_insert",
    "sgv_ketnoitrithuc.json",
)


def fix_ocr_confused_O_and_0(text: str) -> str:
    text = text.upper()
    text = re.sub(r"\bO(\d+)\b", r"0\1", text)
    text = re.sub(r"(\d)\s+O\s+(\d)", r"\1 0 \2", text)
    text = re.sub(r"([A-Z]{2,})\s+O\b", r"\1 0", text)
    text = re.sub(r"\b([A-Z]{2,})\s+O(\d+)\b", r"\1 0\2", text)
    return re.sub(r"\s+", " ", text.strip())


def clean_lesson_title_auto(lesson_parts: List[str]) -> str:
    raw = " ".join(lesson_parts)
    words = re.findall(r"\b[A-Z]+(?:-[A-Z]+)*\b", raw.upper())
    return " ".join(words)


def build_entities_from_item(item: Dict[str, Any]) -> Dict[str, Any]:
    # lesson title
    lesson_parts = item.get("lesson", [])
    lesson_title = " ".join(lesson_parts) if isinstance(lesson_parts, list) else str(lesson_parts)

    # source string
    infor = item.get("infor", {}) or {}
    page = infor.get("page", "") or ""
    source = infor.get("source", "") or ""
    if page != "":
        source = f"{source} - trang {page}" if source else f"trang {page}"

    # collect content from parts
    parts = item.get("parts", []) or []
    all_content: List[str] = []
    front_snippet: List[str] = []

    for idx, part in enumerate(parts):
        topic = part.get("topic", "")
        content = part.get("content", "")

        if topic:
            all_content.append(str(topic))

        if content:
            if isinstance(content, list):
                all_content.extend([str(x) for x in content])
                if idx in [0, 1]:
                    front_snippet.extend([str(x) for x in content])
            else:
                all_content.append(str(content))
                if idx in [0, 1]:
                    front_snippet.append(str(content))

    full_content = "\n\n".join(all_content)

    # text for embedding
    full_content_for_embedding = f"{lesson_title} - {' '.join(front_snippet)}"
    clean_content_for_embedding = fix_ocr_confused_O_and_0(
        clean_lesson_title_auto([full_content_for_embedding])
    )

    return {
        "lesson": lesson_title,
        "content": full_content,
        "source": source,
        "embed_text": clean_content_for_embedding,
    }


def connect_milvus() -> None:
    connect()


def insert_entities_json(json_path: str = DEFAULT_JSON_PATH) -> None:
    print("🚀 Inserting SGV data into Milvus")
    print(f"   JSON: {json_path}")
    print(f"   Collection: {COLLECTION_NAME}")

    # Connect
    connect_milvus()

    # Check collection exists by trying to get it
    try:
        get_collection(COLLECTION_NAME)
    except RuntimeError as e:
        raise RuntimeError(f"Collection '{COLLECTION_NAME}' does not exist. Run setup_milvus.py first.")

    # Load JSON
    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    # Normalize to list
    if isinstance(data, dict):
        data = [data]

    print(f"📦 Loaded {len(data)} items")

    # Build entities and texts for embedding
    print("🔄 Building entities from items...")
    rows: List[Dict[str, Any]] = [build_entities_from_item(item) for item in tqdm(data, desc="Processing items")]

    # Generate embeddings
    print("🧠 Generating embeddings...")
    embedder = LocalEmbedding(verbose=True)
    texts = [row["embed_text"] for row in tqdm(rows, desc="Preparing texts")]
    embeddings = embedder.embed_texts(texts)

    if not embeddings or any(len(vec) != EMBEDDING_DIMENSION for vec in embeddings):
        raise ValueError("Embedding generation failed or wrong dimension")

    # Prepare row-wise data for insert function
    print("📝 Preparing data for insertion...")
    insert_data = []
    for i, (row, embedding) in enumerate(tqdm(zip(rows, embeddings), desc="Preparing data", total=len(rows))):
        insert_data.append({
            "id": f"vector_{i}",
            "lesson": "" if row.get("lesson") is None else str(row.get("lesson")),
            "content": "" if row.get("content") is None else str(row.get("content")),
            "source": "" if row.get("source") is None else str(row.get("source")),
            "embedding": embedding
        })

    # Insert using new milvus_client function
    print("💾 Inserting data into Milvus...")
    insert_result = insert(COLLECTION_NAME, insert_data)

    print(f"✅ Inserted {len(insert_data)} rows. Primary keys: {len(insert_result)}")


def main():
    try:
        json_path = os.environ.get("SGV_JSON_PATH", DEFAULT_JSON_PATH)
        insert_entities_json(json_path)
    except Exception as e:
        print(f"❌ Insert failed: {e}")
        traceback.print_exc()


if __name__ == "__main__":
    main()