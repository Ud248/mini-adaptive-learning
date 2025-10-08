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
        # Bài tập SGK vectors collection
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
            "description": "Bài tập SGK vectors (text + embedding 768D)",
            "enable_dynamic_field": False
        },
        # SGV collection theo yêu cầu (dùng VARCHAR id để đồng bộ với Mongo vector_id)
        "sgv_collection": {
            "fields": [
                {"name": "id", "dtype": DataType.VARCHAR, "is_primary": True, "max_length": 200},
                {"name": "lesson", "dtype": DataType.VARCHAR, "max_length": 2048},
                {"name": "content", "dtype": DataType.VARCHAR, "max_length": 65535},
                {"name": "source", "dtype": DataType.VARCHAR, "max_length": 2048},
                {"name": "embedding", "dtype": DataType.FLOAT_VECTOR, "dim": 768}
            ],
            "description": "SGV content with topic and embeddings",
            "enable_dynamic_field": True
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
        
        # Tạo fields (hỗ trợ cấu hình theo tuple hoặc dict)
        fields = []
        for field_conf in config["fields"]:
            # Cấu hình dạng dict linh hoạt hơn
            if isinstance(field_conf, dict):
                name = field_conf.get("name")
                dtype = field_conf.get("dtype")
                is_primary = field_conf.get("is_primary", False)
                auto_id = field_conf.get("auto_id", False)
                max_length = field_conf.get("max_length")
                dim = field_conf.get("dim")

                if dtype == DataType.FLOAT_VECTOR:
                    field = FieldSchema(name=name, dtype=dtype, dim=dim or 0)
                else:
                    # FieldSchema chấp nhận auto_id chỉ khi là primary key INT64
                    if auto_id:
                        field = FieldSchema(name=name, dtype=dtype, is_primary=is_primary, auto_id=True, max_length=max_length)
                    else:
                        field = FieldSchema(name=name, dtype=dtype, is_primary=is_primary, max_length=max_length)
            else:
                # Back-compat: tuple (name, dtype, is_primary, max_length)
                field_name, dtype, is_primary, max_length = field_conf
                if dtype == DataType.FLOAT_VECTOR:
                    field = FieldSchema(name=field_name, dtype=dtype, dim=max_length)
                else:
                    field = FieldSchema(name=field_name, dtype=dtype, is_primary=is_primary, max_length=max_length if max_length else None)

            fields.append(field)
        
        # Tạo schema và collection
        enable_dynamic_field = config.get("enable_dynamic_field", False)
        schema = CollectionSchema(fields=fields, description=config["description"], enable_dynamic_field=enable_dynamic_field)
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
