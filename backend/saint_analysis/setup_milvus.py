#!/usr/bin/env python3
"""
Script setup nhanh cho Milvus collections
"""

from pymilvus import connections, Collection, FieldSchema, CollectionSchema, DataType, utility

def setup_collections():
    """Setup tất cả collections cần thiết"""
    
    # Kết nối Milvus
    print("Ket noi den Milvus...")
    connections.connect(alias="default", host="localhost", port="19530")
    
    # Collections cần tạo
    collections_config = {
        "profile_student": {
            "fields": [
                ("student_id", DataType.VARCHAR, True, 100),
                ("low_accuracy_skills", DataType.VARCHAR, False, 500),
                ("slow_response_skills", DataType.VARCHAR, False, 500),
                ("embedding_vector", DataType.FLOAT_VECTOR, False, 128)  # Vector field
            ],
            "description": "Hồ sơ học sinh chính"
        },
        "snapshot_student": {
            "fields": [
                ("id", DataType.INT64, True, None),  # Primary key
                ("student_id", DataType.VARCHAR, False, 100),
                ("timestamp", DataType.VARCHAR, False, 50),
                ("low_accuracy_skills", DataType.VARCHAR, False, 500),
                ("slow_response_skills", DataType.VARCHAR, False, 500),
                ("embedding_vector", DataType.FLOAT_VECTOR, False, 128)  # Vector field
            ],
            "description": "Snapshot tiến bộ học sinh"
        },
        "skill_progress_collection": {
            "fields": [
                ("id", DataType.INT64, True, None),  # Primary key
                ("student_id", DataType.VARCHAR, False, 100),
                ("skill_id", DataType.VARCHAR, False, 50),
                ("timestamp", DataType.VARCHAR, False, 50),
                ("accuracy", DataType.FLOAT, False, None),
                ("avg_time", DataType.FLOAT, False, None),
                ("progress_vector", DataType.FLOAT_VECTOR, False, 64)  # Vector field cho progress
            ],
            "description": "Xu hướng tiến bộ kỹ năng"
        }
        ,
        "baitap_collection": {
            "fields": [
                ("id", DataType.INT64, True, None),
                ("baitap_id", DataType.VARCHAR, False, 100),
                ("skill_id", DataType.VARCHAR, False, 100),
                ("question_text", DataType.VARCHAR, False, 2000),
                ("answer", DataType.VARCHAR, False, 500)
            ],
            "description": "Danh mục bài tập/ câu hỏi"
        }
    }
    
    # Tạo từng collection
    for collection_name, config in collections_config.items():
        print(f"\nTao collection: {collection_name}")
        
        # Kiểm tra collection đã tồn tại
        if utility.has_collection(collection_name):
            print(f"Collection '{collection_name}' da ton tai")
            
            # Kiểm tra và tạo index nếu cần
            try:
                collection = Collection(collection_name)
                schema = collection.schema
                vector_fields = [field for field in schema.fields if field.dtype == DataType.FLOAT_VECTOR]
                
                for vector_field in vector_fields:
                    # Kiểm tra index đã tồn tại chưa
                    if collection.has_index():
                        print(f"  - Index da ton tai cho field: {vector_field.name}")
                    else:
                        print(f"  - Tao index cho field: {vector_field.name}")
                        index_params = {
                            "metric_type": "L2",
                            "index_type": "IVF_FLAT",
                            "params": {"nlist": 128}
                        }
                        collection.create_index(field_name=vector_field.name, index_params=index_params)
                        print(f"    ✅ Da tao index cho {vector_field.name}")
            except Exception as e:
                print(f"  ❌ Loi tao index: {e}")
            
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
            print(f"  - Da tao index cho field: {vector_field.name}")
        
        print(f"Da tao collection '{collection_name}' thanh cong")
    
    print(f"\nSetup hoan tat!")
    print(f"Collections hien co: {utility.list_collections()}")

if __name__ == "__main__":
    setup_collections()
