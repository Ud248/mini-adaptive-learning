#!/usr/bin/env python3
"""
Milvus Setup Script - Script thiết lập Milvus cho hệ thống
===========================================================

File này chịu trách nhiệm thiết lập và cấu hình Milvus database cho hệ thống
adaptive learning. Chứa các hàm cụ thể để tạo collections và setup môi trường.

Chức năng chính:
- Tạo các collections mặc định: snapshot_student, skill_progress_collection, baitap_collection, sgv_collection
- Cấu hình schema và indexes cho từng collection
- Setup toàn bộ môi trường Milvus và kiểm tra setup

Sử dụng: python database/milvus/setup_milvus.py
"""

import os
import sys
from dotenv import load_dotenv
from typing import Dict, Any

# Add project root to path
_CURRENT_DIR = os.path.dirname(__file__)
_PROJECT_ROOT = os.path.abspath(os.path.join(_CURRENT_DIR, '..', '..'))
if _PROJECT_ROOT not in sys.path:
    sys.path.insert(0, _PROJECT_ROOT)

# Load environment variables
load_dotenv()

# Import functions from milvus_client
from database.milvus.milvus_client import (
    connect, 
    create_collection,
    list_collections, 
    get_collection_info
)
from pymilvus import DataType

def create_collections_from_config(collections_config: Dict[str, Dict[str, Any]]) -> bool:
    """
    Tạo nhiều collections từ config dictionary
    
    Args:
        collections_config: Dictionary chứa config của các collections
        
    Returns:
        True nếu tất cả thành công
    """
    try:
        connect()
        success_count = 0
        total_count = len(collections_config)
        
        for collection_name, config in collections_config.items():
            try:
                fields = config.get("fields", [])
                description = config.get("description", "")
                enable_dynamic_field = config.get("enable_dynamic_field", False)
                
                if create_collection(collection_name, fields, description, enable_dynamic_field):
                    success_count += 1
                    
            except Exception as e:
                print(f"❌ Failed to create collection '{collection_name}': {e}")
        
        print(f"✅ Created {success_count}/{total_count} collections successfully")
        return success_count == total_count
        
    except Exception as e:
        print(f"❌ Error creating collections from config: {e}")
        raise

def create_default_collections() -> bool:
    """
    Tạo các collections mặc định cho hệ thống
    
    Returns:
        True nếu thành công
    """
    default_config = {
        "baitap_collection": {
            "fields": [
                {"name": "id", "dtype": DataType.VARCHAR, "is_primary": True, "max_length": 100},
                {"name": "question", "dtype": DataType.VARCHAR, "max_length": 65535},
                {"name": "answer", "dtype": DataType.VARCHAR, "max_length": 65535},
                {"name": "lesson", "dtype": DataType.VARCHAR, "max_length": 2048},
                {"name": "subject", "dtype": DataType.VARCHAR, "max_length": 512},
                {"name": "source", "dtype": DataType.VARCHAR, "max_length": 2048},
                {"name": "embedding", "dtype": DataType.FLOAT_VECTOR, "dim": 768}
            ],
            "description": "Bài tập SGK cùng vector content",
            "enable_dynamic_field": False
        },
        "sgv_collection": {
            "fields": [
                {"name": "id", "dtype": DataType.VARCHAR, "is_primary": True, "max_length": 200},
                {"name": "lesson", "dtype": DataType.VARCHAR, "max_length": 2048},
                {"name": "content", "dtype": DataType.VARCHAR, "max_length": 65535},
                {"name": "source", "dtype": DataType.VARCHAR, "max_length": 2048},
                {"name": "embedding", "dtype": DataType.FLOAT_VECTOR, "dim": 768}
            ],
            "description": "Nội dung sách Giáo viên cùng vector content",
            "enable_dynamic_field": True
        }
    }
    
    return create_collections_from_config(default_config)

def setup_milvus_collections() -> bool:
    """
    Setup toàn bộ Milvus collections cho hệ thống
    
    Returns:
        True nếu thành công
    """
    try:
        print("🚀 Setting up Milvus collections...")
        
        # Tạo các collections mặc định
        success = create_default_collections()
        
        if success:
            print("🎉 Milvus collections setup completed successfully!")
            
            # Hiển thị thông tin collections
            collections = list_collections()
            print(f"📋 Available collections: {collections}")
            
            for collection_name in collections:
                try:
                    info = get_collection_info(collection_name)
                    print(f"📊 {collection_name}: {info['num_entities']} entities")
                except Exception as e:
                    print(f"⚠️ Could not get info for {collection_name}: {e}")
        
        return success
        
    except Exception as e:
        print(f"❌ Milvus setup failed: {e}")
        raise

def verify_setup():
    """Kiểm tra setup sử dụng hàm từ milvus_client"""
    print(f"\n🔍 Verifying Milvus setup...")
    
    try:
        collections = list_collections()
        print(f"📋 Collections: {collections}")
        
        for collection_name in collections:
            try:
                info = get_collection_info(collection_name)
                print(f"📊 {collection_name}: {info['num_entities']} entities")
                print(f"   Fields: {[field['name'] for field in info['schema']['fields']]}")
            except Exception as e:
                print(f"⚠️ Could not get info for {collection_name}: {e}")
            
    except Exception as e:
        print(f"❌ Verification error: {e}")

def main():
    """Main function sử dụng các hàm từ milvus_client.py"""
    print("🚀 Milvus Setup for SAINT Analysis")
    print("=" * 50)
    
    try:
        # Sử dụng hàm setup_milvus_collections từ milvus_client.py
        # Hàm này đã bao gồm cả connect và tạo collections
        success = setup_milvus_collections()
        
        if success:
            # Verify setup
            verify_setup()
            
            print(f"\n🎉 Milvus setup completed successfully!")
        else:
            print(f"\n❌ Milvus setup failed!")
            return False
        
    except Exception as e:
        print(f"❌ Setup failed: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    return True

if __name__ == "__main__":
    main()
