#!/usr/bin/env python3
"""
MongoDB Users Insert Script
Seed tài khoản học sinh mẫu với mật khẩu đã băm
"""

import json
import os
from datetime import datetime, timezone
from pymongo import MongoClient
from dotenv import load_dotenv
import hashlib
import secrets

# Load env
load_dotenv()

MONGO_URL = os.getenv("MONGO_URL", "mongodb://localhost:27017")
DATABASE_NAME = os.getenv("DATABASE_NAME", "mini_adaptive_learning")

def hash_password(password: str) -> str:
    """Hash password using SHA-256 with salt (compatible with API)"""
    salt = secrets.token_hex(16)
    password_hash = hashlib.sha256((password + salt).encode('utf-8')).hexdigest()
    return f"{salt}:{password_hash}"

def connect_mongodb():
    try:
        client = MongoClient(MONGO_URL)
        client.admin.command('ping')
        print(f"[OK] Connected to MongoDB at {MONGO_URL}")
        return client
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

def upsert_users(db, users_docs):
    col = db["users"]
    inserted, updated = 0, 0
    for doc in users_docs:
        key = {"email": doc["email"]} if doc.get("email") else {"username": doc["username"]}
        existing = col.find_one(key)
        if existing:
            col.update_one({"_id": existing["_id"]}, {"$set": doc})
            updated += 1
        else:
            col.insert_one(doc)
            inserted += 1
    print(f"[OK] Users upserted. inserted={inserted}, updated={updated}")

def main():
    print("MongoDB Users Insert Script")
    print("=" * 50)

    json_file = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data_insert", "users_sample.json")
    if not os.path.exists(json_file):
        print(f"[ERROR] File not found: {json_file}")
        return

    client = connect_mongodb()
    if not client:
        return

    try:
        db = client[DATABASE_NAME]
        raw_users = load_users_from_json(json_file)
        users_docs = transform_users(raw_users)
        if not users_docs:
            print("[WARNING] No users to insert")
            return
        upsert_users(db, users_docs)
        sample = db["users"].find_one({}, {"email": 1, "role": 1})
        print(f"[INFO] Sample user: {sample}")
        print("[SUCCESS] Done!")
    except Exception as e:
        print(f"[ERROR] Failed: {e}")
        import traceback
        traceback.print_exc()
    finally:
        client.close()

if __name__ == "__main__":
    main()


