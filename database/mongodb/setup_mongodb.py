#!/usr/bin/env python3
"""
MongoDB Setup Script - Script thiết lập MongoDB cho hệ thống
===========================================================

File này chịu trách nhiệm thiết lập và cấu hình MongoDB database cho hệ thống
adaptive learning. Tạo database, collections và indexes cần thiết.

Chức năng chính:
- Tạo database và các collections cần thiết
- Cấu hình indexes cho từng collection
- Kiểm tra và xác minh setup

Sử dụng: python database/mongodb/setup_mongodb.py
"""

import os
import sys
from pymongo import ASCENDING, DESCENDING

# Add project root to path
_CURRENT_DIR = os.path.dirname(__file__)
_PROJECT_ROOT = os.path.abspath(os.path.join(_CURRENT_DIR, '..', '..'))
if _PROJECT_ROOT not in sys.path:
    sys.path.insert(0, _PROJECT_ROOT)

# Import from mongodb_client
from database.mongodb.mongodb_client import (
    connect, create_index, get_collection_info, list_collections
)

def connect_mongodb():
    """Kết nối đến MongoDB sử dụng mongodb_client"""
    try:
        db = connect()
        return db
    except Exception as e:
        print(f"❌ Error connecting to MongoDB: {e}")
        return None

def create_database_and_collections():
    """Tạo database và collections sử dụng mongodb_client
    Xóa collections cũ trước khi tạo mới"""
    db = connect()
    
    # Collections cần tạo
    collections_config = {
        "subjects": {
            "description": "Danh sách môn học",
            "indexes": [
                [("subject_name", 1), {"unique": True, "name": "idx_subject_name_unique"}], 
                [("created_at", -1)] 
            ]
        },
        "grades": {
            "description": "Danh sách khối lớp",
            "indexes": [
                [("grade_name", 1), {"unique": True, "name": "idx_grade_name_unique"}],
                [("created_at", -1)]
            ]
        },
        "skills": {
            "description": "Danh sách kỹ năng",
            "indexes": [
                [("skill_name", 1), ("grade_id", 1), ("subject_id", 1), {"unique": True, "name": "idx_skill_unique_composite"}],
                [("grade_id", 1), ("subject_id", 1)],
                [("created_at", -1)]
            ]
        },
        "users": {
            "description": "Tài khoản người dùng (admin, teacher, student)",
            "indexes": [
                [("email", ASCENDING), {"unique": True}],
                [("username", ASCENDING), {"unique": True}],
                [("role", ASCENDING), ("created_at", DESCENDING)],
                [("created_at", DESCENDING)]
            ]
        },
        "placement_questions": {
            "description": "Câu hỏi của bài kiểm tra đầu vào",
            "indexes": [
                [("skill_id", ASCENDING), ("difficulty", ASCENDING)],
                [("skill_id", ASCENDING), ("type", ASCENDING)],
                [("status", ASCENDING), ("skill_id", ASCENDING)],
                [("created_by", ASCENDING)],
                [("created_at", DESCENDING)],
                [("updated_at", DESCENDING)]
            ]
        },
        "teacher_books": {
            "description": "Sách giáo viên - mỗi document là một bài học",
            "indexes": [
                [("grade", ASCENDING)],
                [("subject", ASCENDING)],
                [("lesson", ASCENDING)],
                [("metadata.tags", ASCENDING)],
                [("vector_id", ASCENDING)]
            ]
        },
        "textbook_exercises": {
            "description": "Bài tập SGK đã chuẩn hoá (mỗi document là một bài tập)",
            "indexes": [
                [("lesson", ASCENDING)],
                [("subject", ASCENDING)],
                [("chapter", ASCENDING)],
                [("vector_id", ASCENDING), {"unique": True}]
            ]
        },
        "profile_student": {
            "description": "Hồ sơ học sinh từ SAINT analysis",
            "indexes": [
                [("student_email", ASCENDING), {"unique": True}],
                [("username", ASCENDING), {"unique": True}],
                [("created_at", DESCENDING)],
                [("updated_at", DESCENDING)]
            ]
        }
    }
    
    print(f"\nDropping and recreating collections and indexes...")
    
    for collection_name, config in collections_config.items():
        print(f"\nSetting up collection: {collection_name}")
        print(f"   Description: {config['description']}")
        
        # Xóa collection cũ nếu tồn tại
        try:
            db[collection_name].drop()
            print(f"   🗑️  Dropped existing collection")
        except Exception as e:
            print(f"   ℹ️  Collection does not exist (first time setup)")
        
        # Tạo indexes sử dụng mongodb_client
        for index_spec in config['indexes']:
            try:
                # Xác định xem phần tử cuối có phải là options không
                if len(index_spec) > 0 and isinstance(index_spec[-1], dict):
                    # Có options ở cuối
                    index_fields_list = index_spec[:-1]
                    index_options = index_spec[-1]
                else:
                    # Không có options
                    index_fields_list = index_spec
                    index_options = {}
                
                # index_fields_list là list các tuples: [("field1", direction), ("field2", direction), ...]
                # Cần chuyển thành format cho mongodb_client
                index_spec_for_client = list(index_fields_list)
                
                # Sử dụng mongodb_client để tạo index
                if index_options:
                    create_index(collection_name, index_spec_for_client, 
                               unique=index_options.get('unique', False),
                               background=index_options.get('background', True))
                else:
                    create_index(collection_name, index_spec_for_client)
                print(f"   Index created: {index_fields_list}")
            except Exception as e:
                print(f"   Index warning: {e}")
    
    return db

def verify_setup():
    """Kiểm tra setup sử dụng mongodb_client"""
    print(f"\nVerifying setup...")
    
    collections = list_collections()
    print(f"Collections: {collections}")
    
    for collection_name in collections:
        try:
            info = get_collection_info(collection_name)
            print(f"\n{collection_name}:")
            print(f"   Documents: {info['count']}")
            print(f"   Indexes: {len(info['indexes'])}")
            for idx in info['indexes']:
                print(f"     - {idx['name']}: {idx['key']}")
        except Exception as e:
            print(f"   Could not get info for {collection_name}: {e}")

def main():
    """Main function"""
    print("MongoDB Setup for Quiz System")
    print("=" * 50)
    
    try:
        # Create database and collections
        db = create_database_and_collections()
        
        # Verify setup
        verify_setup()
        
        print(f"\nMongoDB setup completed successfully!")
        
    except Exception as e:
        print(f"Setup failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
