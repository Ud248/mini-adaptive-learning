#!/usr/bin/env python3
"""
MongoDB Users Insert Script - Script nhập dữ liệu users vào MongoDB
================================================================

File này chịu trách nhiệm nhập dữ liệu users vào MongoDB collection.
Tạo tài khoản học sinh mẫu với mật khẩu đã băm và thông tin cơ bản.

Chức năng chính:
- Tạo tài khoản học sinh mẫu với mật khẩu đã hash
- Nhập dữ liệu vào collection users trong MongoDB
- Tạo indexes cho collection users

Sử dụng: python database/mongodb/insert_users.py
"""

import json
import os
import sys
from datetime import datetime, timezone
import hashlib
import secrets
from tqdm import tqdm

# Add project root to path
_CURRENT_DIR = os.path.dirname(__file__)
_PROJECT_ROOT = os.path.abspath(os.path.join(_CURRENT_DIR, '..', '..'))
if _PROJECT_ROOT not in sys.path:
    sys.path.insert(0, _PROJECT_ROOT)

# Import from mongodb_client
from database.mongodb.mongodb_client import (
    connect, get_collection, insert, create_index, 
    get_collection_info, list_collections, find_one
)

def hash_password(password: str) -> str:
    """Hash password using SHA-256 with salt (compatible with API)"""
    salt = secrets.token_hex(16)
    password_hash = hashlib.sha256((password + salt).encode('utf-8')).hexdigest()
    return f"{salt}:{password_hash}"

def connect_mongodb():
    """Kết nối đến MongoDB sử dụng mongodb_client"""
    try:
        db = connect()
        return db
    except Exception as e:
        print(f"[ERROR] Error connecting to MongoDB: {e}")
        return None

def load_users_from_json(file_path: str):
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            users = json.load(f)
        print(f"[INFO] Loaded {len(users)} users from {file_path}")
        return users
    except Exception as e:
        print(f"[ERROR] Error loading users: {e}")
        return []

def transform_users(raw_users):
    docs = []
    for u in raw_users:
        email = u.get("email", "").strip().lower()
        username = u.get("username", "").strip()
        role = (u.get("role") or "student").strip()
        full_name = u.get("full_name") or ""
        plain_password = u.get("password") or "123456"
        
        # Clean and validate password
        plain_password = str(plain_password).strip()
        if not plain_password:
            plain_password = "123456"

        if not email and not username:
            print("[WARNING] Skip user with no email/username")
            continue

        try:
            password_hash = hash_password(plain_password)
        except Exception as e:
            print(f"[ERROR] Error hashing password for user {email or username}: {e}")
            print(f"   Password length: {len(plain_password.encode('utf-8'))} bytes")
            print(f"   Password preview: {repr(plain_password[:20])}")
            continue

        docs.append({
            "email": email,
            "username": username,
            "role": role,
            "full_name": full_name,
            "password_hash": password_hash,
            "created_at": datetime.now(timezone.utc),
            "updated_at": datetime.now(timezone.utc),
            "status": "active"
        })
    return docs

def upsert_users(users_docs):
    """Upsert users sử dụng mongodb_client"""
    try:
        # Tạo indexes
        create_index("users", "email", unique=True, background=True)
        create_index("users", "username", unique=True, background=True)
        create_index("users", "role")
        create_index("users", "status")
        # Upsert users với progress bar
        inserted, updated = 0, 0
        for doc in tqdm(users_docs, desc="Upserting users", unit="user"):
            key = {"email": doc["email"]} if doc.get("email") else {"username": doc["username"]}
            existing = find_one("users", key)
            if existing:
                update("users", {"_id": existing["_id"]}, {"$set": doc})
                updated += 1
            else:
                insert("users", doc)
                inserted += 1
        print(f"[OK] Users upserted. inserted={inserted}, updated={updated}")
        
    except Exception as e:
        print(f"[ERROR] Error upserting users: {e}")
        return False

def main():
    print("MongoDB Users Insert Script")
    print("=" * 50)

    json_file = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data_insert", "users_sample.json")
    if not os.path.exists(json_file):
        print(f"[ERROR] File not found: {json_file}")
        return

    db = connect_mongodb()
    if db is None:
        return

    try:
        raw_users = load_users_from_json(json_file)
        users_docs = transform_users(raw_users)
        if not users_docs:
            print("[WARNING] No users to insert")
            return
        upsert_users(users_docs)
        sample = find_one("users", {}, {"email": 1, "role": 1})
        print(f"[INFO] Sample user: {sample}")
        print("[SUCCESS] Done!")
    except Exception as e:
        print(f"[ERROR] Failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()


