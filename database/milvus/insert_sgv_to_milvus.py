#!/usr/bin/env python3
"""
Insert SGV JSON into Milvus `sgv_collection`.

Reads `database/data_insert/sgv_ketnoitrithuc.json`, builds content and
source strings, generates 768-dim embeddings using local Vietnamese
sentence-transformer, and inserts into Milvus collection `sgv_collection`.
"""

import json
import os
import sys
import re
import traceback
from typing import List, Dict, Any

from pymilvus import connections, utility, Collection

# Ensure project root is on sys.path when running as a script
_CURRENT_DIR = os.path.dirname(__file__)
_PROJECT_ROOT = os.path.abspath(os.path.join(_CURRENT_DIR, '..', '..'))
if _PROJECT_ROOT not in sys.path:
    sys.path.insert(0, _PROJECT_ROOT)

# Local modules (absolute import from project root)
from database.embeddings.local_embedder import LocalEmbedding, EMBEDDING_DIMENSION


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
    connections.connect(alias=MILVUS_ALIAS, host=os.getenv("MILVUS_HOST", "localhost"), port=os.getenv("MILVUS_PORT", "19530"))


def insert_entities_json(json_path: str = DEFAULT_JSON_PATH) -> None:
    print("🚀 Inserting SGV data into Milvus")
    print(f"   JSON: {json_path}")
    print(f"   Collection: {COLLECTION_NAME}")

    # Connect
    connect_milvus()

    # Check collection
    if not utility.has_collection(COLLECTION_NAME):
        raise RuntimeError(f"Collection '{COLLECTION_NAME}' does not exist. Run setup_milvus.py first.")

    # Load JSON
    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    # Normalize to list
    if isinstance(data, dict):
        data = [data]

    print(f"📦 Loaded {len(data)} items")

    # Build entities and texts for embedding
    rows: List[Dict[str, Any]] = [build_entities_from_item(item) for item in data]

    # Generate embeddings
    embedder = LocalEmbedding(verbose=True)
    texts = [row["embed_text"] for row in rows]
    embeddings = embedder.embed_texts(texts)

    # Prepare column-wise insert (order must match schema: id, lesson, content, source, embedding)
    # Use sequential vector IDs matching list order: vector_0, vector_1, ...
    ids = [f"vector_{i}" for i in range(len(rows))]
    lessons = ["" if row.get("lesson") is None else str(row.get("lesson")) for row in rows]
    contents = ["" if row.get("content") is None else str(row.get("content")) for row in rows]
    sources = ["" if row.get("source") is None else str(row.get("source")) for row in rows]

    if not embeddings or any(len(vec) != EMBEDDING_DIMENSION for vec in embeddings):
        raise ValueError("Embedding generation failed or wrong dimension")

    # Insert
    collection = Collection(COLLECTION_NAME)
    entities = [
        ids,            # id (VARCHAR PK)
        lessons,        # lesson (VARCHAR)
        contents,       # content (VARCHAR)
        sources,        # source (VARCHAR)
        embeddings,     # embedding (FLOAT_VECTOR[768])
    ]

    # Match schema order (id is auto_id, so schema fields should be [id, lesson, content, source, embedding])
    insert_result = collection.insert(entities)
    collection.flush()

    print(f"✅ Inserted {len(lessons)} rows. LSN: {insert_result.insert_count}")


def main():
    try:
        json_path = os.environ.get("SGV_JSON_PATH", DEFAULT_JSON_PATH)
        insert_entities_json(json_path)
    except Exception as e:
        print(f"❌ Insert failed: {e}")
        traceback.print_exc()


if __name__ == "__main__":
    main()


