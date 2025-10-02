#!/usr/bin/env python3
"""
MongoDB Setup Script
Tạo database, collections và indexes cho hệ thống quiz
"""

from pymongo import MongoClient, ASCENDING, DESCENDING
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# MongoDB connection
MONGO_URL = os.getenv("MONGO_URL", "mongodb://localhost:27017")
DATABASE_NAME = os.getenv("DATABASE_NAME", "quiz_system")

def connect_mongodb():
    """Kết nối đến MongoDB"""
    try:
        client = MongoClient(MONGO_URL)
        # Test connection
        client.admin.command('ping')
        print(f"✅ Connected to MongoDB at {MONGO_URL}")
        return client
    except Exception as e:
        print(f"❌ Error connecting to MongoDB: {e}")
        return None

def create_database_and_collections(client):
    """Tạo database và collections"""
    db = client[DATABASE_NAME]
    
    # Collections cần tạo
    collections_config = {
        "questions": {
            "description": "Câu hỏi quiz",
            "indexes": [
                [("question_id", ASCENDING), {"unique": True}],
                [("grade", ASCENDING), ("subject", ASCENDING), ("skill", ASCENDING)],
                [("skill", ASCENDING), ("difficulty", ASCENDING)],
                [("grade", ASCENDING), ("subject", ASCENDING)],
                [("created_at", DESCENDING)]
            ]
        },
        "users": {
            "description": "Tài khoản người dùng (học sinh, giáo viên, admin)",
            "indexes": [
                [("email", ASCENDING), {"unique": True}],
                [("username", ASCENDING), {"unique": True}],
                [("role", ASCENDING), ("created_at", DESCENDING)],
                [("created_at", DESCENDING)]
            ]
        },
        "skills": {
            "description": "Danh sách kỹ năng",
            "indexes": [
                [("skill_id", ASCENDING), {"unique": True}],
                [("grade", ASCENDING), ("subject", ASCENDING)]
            ]
        },
        "subjects": {
            "description": "Danh sách môn học",
            "indexes": [
                [("subject_id", ASCENDING), {"unique": True}],
                [("grade", ASCENDING)]
            ]
        },
        "quiz_sessions": {
            "description": "Phiên làm bài quiz",
            "indexes": [
                [("quiz_id", ASCENDING), {"unique": True}],
                [("student_id", ASCENDING), ("created_at", DESCENDING)],
                [("grade", ASCENDING), ("subject", ASCENDING)]
            ]
        }
    }
    
    print(f"\n📊 Creating collections in database '{DATABASE_NAME}'...")
    
    for collection_name, config in collections_config.items():
        print(f"\n📁 Creating collection: {collection_name}")
        print(f"   Description: {config['description']}")
        
        # Tạo collection (nếu chưa tồn tại)
        if collection_name not in db.list_collection_names():
            db.create_collection(collection_name)
            print(f"   ✅ Collection '{collection_name}' created")
        else:
            print(f"   ℹ️  Collection '{collection_name}' already exists")
        
        # Tạo indexes
        collection = db[collection_name]
        for index_spec in config['indexes']:
            try:
                if isinstance(index_spec[0], tuple):
                    # Compound index
                    index_fields = index_spec[0]
                    index_options = index_spec[1] if len(index_spec) > 1 else {}
                else:
                    # Single field index
                    index_fields = index_spec[0]
                    index_options = {}
                
                collection.create_index(index_fields, **index_options)
                print(f"   ✅ Index created: {index_fields}")
            except Exception as e:
                print(f"   ⚠️  Index warning: {e}")
    
    return db

def verify_setup(db):
    """Kiểm tra setup"""
    print(f"\n🔍 Verifying setup...")
    
    collections = db.list_collection_names()
    print(f"📋 Collections: {collections}")
    
    for collection_name in collections:
        collection = db[collection_name]
        count = collection.count_documents({})
        indexes = list(collection.list_indexes())
        
        print(f"\n📊 {collection_name}:")
        print(f"   Documents: {count}")
        print(f"   Indexes: {len(indexes)}")
        for idx in indexes:
            print(f"     - {idx['name']}: {idx['key']}")

def main():
    """Main function"""
    print("🚀 MongoDB Setup for Quiz System")
    print("=" * 50)
    
    # Connect to MongoDB
    client = connect_mongodb()
    if not client:
        return
    
    try:
        # Create database and collections
        db = create_database_and_collections(client)
        
        # Verify setup
        verify_setup(db)
        
        print(f"\n🎉 MongoDB setup completed successfully!")
        print(f"📊 Database: {DATABASE_NAME}")
        print(f"🔗 Connection: {MONGO_URL}")
        
    except Exception as e:
        print(f"❌ Setup failed: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        client.close()

if __name__ == "__main__":
    main()
