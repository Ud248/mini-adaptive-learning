#!/usr/bin/env python3
"""
Normalize SGK JSON and insert vectors into Milvus collection `sgk_exercises_vectors`.

Rules (matching MongoDB normalization):
- Remove `difficulty`.
- Convert string "null" answer to None.
- Add metadata (not stored in Milvus, only used if needed).
- Build vector embedding from text fields using absolute path to database/embeddings/local_embedder.py
  Text used for embedding: question + " | " + lesson + " | " + subject + " | " + source
- id (primary key): "vector_<index>"

Milvus schema expectations for `sgk_exercises_vectors`:
  - id: VARCHAR (PK) or a separate INT64 PK with id as VARCHAR field (we store id as VARCHAR here)
  - question: VARCHAR
  - answer: VARCHAR
  - lesson: VARCHAR
  - subject: VARCHAR
  - source: VARCHAR
  - embedding: FLOAT_VECTOR dim=768

Note: Ensure collection exists with the above schema before running, or extend this script to create it.
"""

import json
import os
import sys
from typing import Any, Dict, List, Optional

from pymilvus import connections, utility, Collection

# Ensure project root in path
_CURRENT_DIR = os.path.dirname(__file__)
_PROJECT_ROOT = os.path.abspath(os.path.join(_CURRENT_DIR, '..', '..'))
if _PROJECT_ROOT not in sys.path:
    sys.path.insert(0, _PROJECT_ROOT)

from database.embeddings.local_embedder import LocalEmbedding, EMBEDDING_DIMENSION


MILVUS_ALIAS = "default"
COLLECTION_NAME = "baitap_collection"

DEFAULT_JSON_1 = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data_insert", "sgk-toan-1-ket-noi-tri-thuc-tap-1.json")
DEFAULT_JSON_2 = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data_insert", "sgk-toan-1-ket-noi-tri-thuc-tap-2.json")


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
    connections.connect(alias=MILVUS_ALIAS, host=os.getenv("MILVUS_HOST", "localhost"), port=os.getenv("MILVUS_PORT", "19530"))


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
    docs = [normalize_item(it) for it in items]

    # Connect Milvus
    connect_milvus()
    if not utility.has_collection(COLLECTION_NAME):
        raise RuntimeError(f"Collection '{COLLECTION_NAME}' does not exist. Please create it first.")

    # Prepare embeddings
    embedder = LocalEmbedding(verbose=True)
    texts = [build_text_for_embedding(doc) for doc in docs]
    embeddings = embedder.embed_texts(texts)

    # Build columns for insert; schema expected order: id, question, answer, lesson, subject, source, embedding
    ids: List[str] = []
    questions: List[Optional[str]] = []
    answers: List[Optional[str]] = []
    lessons: List[Optional[str]] = []
    subjects: List[Optional[str]] = []
    sources: List[Optional[str]] = []
    vectors: List[List[float]] = []

    for i, doc in enumerate(docs):
        ids.append(f"vector_{i}")
        # Milvus VARCHAR fields must be strings; coerce None -> ""
        q = doc.get("question")
        a = doc.get("answer")
        lsn = doc.get("lesson")
        subj = doc.get("subject")
        src = doc.get("source")
        questions.append("" if q is None else str(q))
        answers.append("" if a is None else str(a))
        lessons.append("" if lsn is None else str(lsn))
        subjects.append("" if subj is None else str(subj))
        sources.append("" if src is None else str(src))
        vec = embeddings[i] if i < len(embeddings) else [0.0] * EMBEDDING_DIMENSION
        vectors.append(vec)

    collection = Collection(COLLECTION_NAME)
    entities = [
        ids,
        questions,
        answers,
        lessons,
        subjects,
        sources,
        vectors,
    ]

    res = collection.insert(entities)
    collection.flush()
    print(f"✅ Inserted {len(ids)} vectors into {COLLECTION_NAME}")


if __name__ == "__main__":
    main()


