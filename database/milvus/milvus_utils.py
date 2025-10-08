#!/usr/bin/env python3
"""
Milvus Utils
Tiện ích kết nối và thao tác collection cho các script đồng bộ.
"""

from pymilvus import connections, Collection, FieldSchema, CollectionSchema, DataType, utility
import os
from dotenv import load_dotenv

load_dotenv()

MILVUS_HOST = os.getenv("MILVUS_HOST", "localhost")
MILVUS_PORT = os.getenv("MILVUS_PORT", "19530")

def connect() -> None:
    connections.connect(alias="default", host=MILVUS_HOST, port=MILVUS_PORT)

def get_collection(name: str) -> Collection:
    if not utility.has_collection(name):
        raise RuntimeError(f"Collection '{name}' không tồn tại. Hãy chạy setup_milvus.py trước.")
    col = Collection(name)
    col.load()
    return col


