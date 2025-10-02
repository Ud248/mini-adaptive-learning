#!/usr/bin/env python3
"""
Milvus Setup Script
Tạo collections và indexes cho hệ thống SAINT Analysis
"""

from pymilvus import connections, Collection, FieldSchema, CollectionSchema, DataType, utility
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Milvus connection
MILVUS_HOST = os.getenv("MILVUS_HOST", "localhost")
MILVUS_PORT = os.getenv("MILVUS_PORT", "19530")

def connect_milvus():
    """Kết nối đến Milvus"""
    try:
        connections.connect(
            alias="default",
            host=MILVUS_HOST,
            port=MILVUS_PORT
        )
        print(f"✅ Connected to Milvus at {MILVUS_HOST}:{MILVUS_PORT}")
        return True
    except Exception as e:
        print(f"❌ Error connecting to Milvus: {e}")
        return False

def create_collections():
    """Tạo các collections cần thiết"""
    
    # Collections configuration
    collections_config = {
        "profile_student": {
            "fields": [
                ("student_id", DataType.VARCHAR, True, 100),
                ("low_accuracy_skills", DataType.VARCHAR, False, 500),
                ("slow_response_skills", DataType.VARCHAR, False, 500),
                ("embedding_vector", DataType.FLOAT_VECTOR, False, 128)
            ],
            "description": "Hồ sơ học sinh chính"
        },
        "snapshot_student": {
            "fields": [
                ("id", DataType.INT64, True, None),
                ("student_id", DataType.VARCHAR, False, 100),
                ("timestamp", DataType.VARCHAR, False, 50),
                ("low_accuracy_skills", DataType.VARCHAR, False, 500),
                ("slow_response_skills", DataType.VARCHAR, False, 500),
                ("embedding_vector", DataType.FLOAT_VECTOR, False, 128)
            ],
            "description": "Snapshot tiến bộ học sinh"
        },
        "skill_progress_collection": {
            "fields": [
                ("id", DataType.INT64, True, None),
                ("student_id", DataType.VARCHAR, False, 100),
                ("skill_id", DataType.VARCHAR, False, 50),
                ("timestamp", DataType.VARCHAR, False, 50),
                ("accuracy", DataType.FLOAT, False, None),
                ("avg_time", DataType.FLOAT, False, None),
                ("progress_vector", DataType.FLOAT_VECTOR, False, 64)
            ],
            "description": "Xu hướng tiến bộ kỹ năng"
        },
        "baitap_collection": {
            "fields": [
                ("id", DataType.INT64, True, None),
                ("baitap_id", DataType.VARCHAR, False, 100),
                ("skill_id", DataType.VARCHAR, False, 100),
                ("question_text", DataType.VARCHAR, False, 2000),
                ("answer", DataType.VARCHAR, False, 500)
            ],
            "description": "Danh mục bài tập/câu hỏi"
        }
    }
    
    print(f"\n📊 Creating Milvus collections...")
    
    for collection_name, config in collections_config.items():
        print(f"\n📁 Creating collection: {collection_name}")
        print(f"   Description: {config['description']}")
        
        # Kiểm tra collection đã tồn tại
        if utility.has_collection(collection_name):
            print(f"   ℹ️  Collection '{collection_name}' already exists")
            
            # Kiểm tra và tạo index nếu cần
            try:
                collection = Collection(collection_name)
                schema = collection.schema
                vector_fields = [field for field in schema.fields if field.dtype == DataType.FLOAT_VECTOR]
                
                for vector_field in vector_fields:
                    if collection.has_index():
                        print(f"   ✅ Index already exists for field: {vector_field.name}")
                    else:
                        print(f"   🔧 Creating index for field: {vector_field.name}")
                        index_params = {
                            "metric_type": "L2",
                            "index_type": "IVF_FLAT",
                            "params": {"nlist": 128}
                        }
                        collection.create_index(field_name=vector_field.name, index_params=index_params)
                        print(f"   ✅ Index created for {vector_field.name}")
            except Exception as e:
                print(f"   ⚠️  Index warning: {e}")
            
            continue
        
        # Tạo fields
        fields = []
        for field_name, dtype, is_primary, max_length in config["fields"]:
            if dtype == DataType.FLOAT_VECTOR:
                # Vector field cần dim parameter
                field = FieldSchema(
                    name=field_name,
                    dtype=dtype,
                    dim=max_length  # max_length chứa dimension cho vector
                )
            else:
                # Regular field
                field = FieldSchema(
                    name=field_name,
                    dtype=dtype,
                    is_primary=is_primary,
                    max_length=max_length if max_length else None
                )
            fields.append(field)
        
        # Tạo schema và collection
        schema = CollectionSchema(fields=fields, description=config["description"])
        collection = Collection(collection_name, schema)
        
        # Tạo index cho vector fields
        vector_fields = [field for field in fields if field.dtype == DataType.FLOAT_VECTOR]
        for vector_field in vector_fields:
            index_params = {
                "metric_type": "L2",
                "index_type": "IVF_FLAT",
                "params": {"nlist": 128}
            }
            collection.create_index(field_name=vector_field.name, index_params=index_params)
            print(f"   ✅ Index created for field: {vector_field.name}")
        
        print(f"   ✅ Collection '{collection_name}' created successfully")

def verify_setup():
    """Kiểm tra setup"""
    print(f"\n🔍 Verifying Milvus setup...")
    
    try:
        collections = utility.list_collections()
        print(f"📋 Collections: {collections}")
        
        for collection_name in collections:
            collection = Collection(collection_name)
            collection.load()
            count = collection.num_entities
            print(f"📊 {collection_name}: {count} entities")
            
            # Show schema
            schema = collection.schema
            print(f"   Fields: {[field.name for field in schema.fields]}")
            
    except Exception as e:
        print(f"❌ Verification error: {e}")

def main():
    """Main function"""
    print("🚀 Milvus Setup for SAINT Analysis")
    print("=" * 50)
    
    # Connect to Milvus
    if not connect_milvus():
        return
    
    try:
        # Create collections
        create_collections()
        
        # Verify setup
        verify_setup()
        
        print(f"\n🎉 Milvus setup completed successfully!")
        print(f"🔗 Connection: {MILVUS_HOST}:{MILVUS_PORT}")
        
    except Exception as e:
        print(f"❌ Setup failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
