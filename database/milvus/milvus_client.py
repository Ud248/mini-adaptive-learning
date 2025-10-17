#!/usr/bin/env python3
"""
Milvus Client - Thư viện CRUD cho Milvus Vector Database
========================================================

File này cung cấp các hàm CRUD cơ bản để tương tác với Milvus collections.
Được thiết kế để các module khác có thể import và sử dụng.

Chức năng chính:
- Kết nối và quản lý kết nối Milvus
- Thao tác CRUD cơ bản: insert, update, delete, search, query
- Tạo và quản lý collections
- Tìm kiếm vector similarity với metadata filtering

Các hàm CRUD:
- insert(): Thêm dữ liệu mới (chỉ insert, không kiểm tra duplicate)
- upsert(): Insert hoặc update dựa trên primary key (khuyến nghị sử dụng)
- update(): Cập nhật records hiện có dựa trên expression
- replace(): Thay thế hoàn toàn records (delete + insert)
- delete(): Xóa records dựa trên expression
- search(): Tìm kiếm vector similarity
- query(): Query dữ liệu với metadata filtering
"""

from pymilvus import connections, Collection, FieldSchema, CollectionSchema, DataType, utility
import os
from dotenv import load_dotenv
from typing import List, Dict, Any, Optional, Union
import logging

load_dotenv()

MILVUS_HOST = os.getenv("MILVUS_HOST", "localhost")
MILVUS_PORT = os.getenv("MILVUS_PORT", "19530")

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def connect() -> None:
    """Kết nối đến Milvus"""
    try:
        connections.connect(alias="default", host=MILVUS_HOST, port=MILVUS_PORT)
        logger.info(f"✅ Connected to Milvus at {MILVUS_HOST}:{MILVUS_PORT}")
    except Exception as e:
        logger.error(f"❌ Error connecting to Milvus: {e}")
        raise

def get_collection(name: str) -> Collection:
    """Lấy collection và load nó"""
    if not utility.has_collection(name):
        raise RuntimeError(f"Collection '{name}' không tồn tại. Hãy chạy setup_milvus.py trước.")
    col = Collection(name)
    col.load()
    return col

def insert(collection_name: str, data: List[Dict[str, Any]]) -> List[Union[int, str]]:
    """
    Thêm dữ liệu mới vào collection (chỉ insert, không update)
    
    Args:
        collection_name: Tên collection
        data: Danh sách các dictionary chứa dữ liệu cần insert
        
    Returns:
        List các ID của records đã được insert
        
    Note:
        - Chỉ thêm dữ liệu mới, không kiểm tra duplicate
        - Sử dụng khi chắc chắn dữ liệu chưa tồn tại
        - Nếu muốn insert hoặc update, sử dụng upsert()
    """
    try:
        connect()
        collection = get_collection(collection_name)
        
        # Chuẩn bị dữ liệu theo format của Milvus
        insert_data = []
        for record in data:
            insert_data.append(record)
        
        # Insert dữ liệu
        result = collection.insert(insert_data)
        collection.flush()
        
        logger.info(f"✅ Inserted {len(data)} records into {collection_name}")
        return result.primary_keys
        
    except Exception as e:
        logger.error(f"❌ Error inserting data into {collection_name}: {e}")
        raise

def delete(collection_name: str, expr: str) -> bool:
    """
    Xóa dữ liệu từ collection dựa trên expression
    
    Args:
        collection_name: Tên collection
        expr: Expression để filter records cần xóa (ví dụ: 'id == "123"')
        
    Returns:
        True nếu thành công
    """
    try:
        connect()
        collection = get_collection(collection_name)
        
        # Xóa dữ liệu
        result = collection.delete(expr)
        collection.flush()
        
        logger.info(f"✅ Deleted records from {collection_name} with expr: {expr}")
        return True
        
    except Exception as e:
        logger.error(f"❌ Error deleting data from {collection_name}: {e}")
        raise

def update(collection_name: str, expr: str, data: Dict[str, Any]) -> bool:
    """
    Cập nhật dữ liệu trong collection bằng cách sử dụng upsert
    
    Args:
        collection_name: Tên collection
        expr: Expression để filter records cần update
        data: Dictionary chứa các field và giá trị cần update
        
    Returns:
        True nếu thành công
    """
    try:
        connect()
        collection = get_collection(collection_name)
        
        # Lấy records cần update
        existing_records = collection.query(expr=expr, output_fields=["*"])
        
        if not existing_records:
            logger.warning(f"No records found matching expr: {expr}")
            return False
        
        # Cập nhật records và sử dụng upsert
        updated_records = []
        for record in existing_records:
            updated_record = record.copy()
            updated_record.update(data)
            updated_records.append(updated_record)
        
        # Sử dụng upsert thay vì delete + insert
        result = collection.upsert(updated_records)
        collection.flush()
        
        logger.info(f"✅ Updated {len(updated_records)} records in {collection_name}")
        return True
        
    except Exception as e:
        logger.error(f"❌ Error updating data in {collection_name}: {e}")
        raise

def search(collection_name: str, 
          vector_field: str,
          query_vectors: List[List[float]],
          anns_field: Optional[str] = None,
          param: Optional[Dict[str, Any]] = None,
          limit: int = 10,
          expr: Optional[str] = None,
          output_fields: Optional[List[str]] = None) -> List[Dict[str, Any]]:
    """
    Tìm kiếm vector similarity với metadata filtering
    
    Args:
        collection_name: Tên collection
        vector_field: Tên field chứa vector
        query_vectors: Danh sách query vectors
        anns_field: Tên field để search (mặc định = vector_field)
        param: Tham số search (metric_type, nprobe, etc.)
        limit: Số lượng kết quả trả về
        expr: Expression để filter metadata
        output_fields: Danh sách fields cần trả về
        
    Returns:
        List các kết quả search
    """
    try:
        connect()
        collection = get_collection(collection_name)
        
        # Thiết lập tham số mặc định
        if anns_field is None:
            anns_field = vector_field
            
        if param is None:
            param = {
                "metric_type": "L2",
                "params": {"nprobe": 10}
            }
        
        if output_fields is None:
            output_fields = ["*"]
        
        # Thực hiện search
        search_params = {
            "data": query_vectors,
            "anns_field": anns_field,
            "param": param,
            "limit": limit,
            "output_fields": output_fields
        }
        
        if expr:
            search_params["expr"] = expr
        
        results = collection.search(**search_params)
        
        # Format kết quả - flatten để trả về list of records thay vì nested list
        formatted_results = []
        for hits in results:
            for hit in hits:
                hit_data = {
                    "id": hit.id,
                    "distance": hit.distance,
                    "entity": hit.entity
                }
                formatted_results.append(hit_data)
        
        logger.info(f"✅ Search completed in {collection_name}, found {len(formatted_results)} result sets")
        return formatted_results
        
    except Exception as e:
        logger.error(f"❌ Error searching in {collection_name}: {e}")
        raise

def query(collection_name: str, 
          expr: str,
          output_fields: Optional[List[str]] = None,
          limit: Optional[int] = None,
          offset: Optional[int] = None) -> List[Dict[str, Any]]:
    """
    Query dữ liệu với metadata filtering
    
    Args:
        collection_name: Tên collection
        expr: Expression để filter
        output_fields: Danh sách fields cần trả về
        limit: Giới hạn số lượng kết quả
        offset: Offset cho pagination
        
    Returns:
        List các kết quả query
    """
    try:
        connect()
        collection = get_collection(collection_name)
        
        if output_fields is None:
            output_fields = ["*"]
        
        # Thực hiện query
        query_params = {
            "expr": expr,
            "output_fields": output_fields
        }
        
        if limit is not None:
            query_params["limit"] = limit
        if offset is not None:
            query_params["offset"] = offset
        
        results = collection.query(**query_params)
        
        logger.info(f"✅ Query completed in {collection_name}, found {len(results)} records")
        return results
        
    except Exception as e:
        logger.error(f"❌ Error querying {collection_name}: {e}")
        raise

def upsert(collection_name: str, data: List[Dict[str, Any]]) -> List[Union[int, str]]:
    """
    Upsert dữ liệu (insert hoặc update nếu đã tồn tại dựa trên primary key)
    
    Args:
        collection_name: Tên collection
        data: Danh sách các dictionary chứa dữ liệu
        
    Returns:
        List các ID của records
    """
    try:
        connect()
        collection = get_collection(collection_name)
        
        # Upsert dữ liệu
        result = collection.upsert(data)
        collection.flush()
        
        logger.info(f"✅ Upserted {len(data)} records into {collection_name}")
        return result.primary_keys
        
    except Exception as e:
        logger.error(f"❌ Error upserting data into {collection_name}: {e}")
        raise

def replace(collection_name: str, expr: str, data: List[Dict[str, Any]]) -> bool:
    """
    Thay thế hoàn toàn records (delete + insert)
    
    Args:
        collection_name: Tên collection
        expr: Expression để filter records cần thay thế
        data: Danh sách các dictionary chứa dữ liệu mới
        
    Returns:
        True nếu thành công
    """
    try:
        connect()
        collection = get_collection(collection_name)
        
        # Xóa records cũ
        collection.delete(expr)
        
        # Insert dữ liệu mới
        if data:
            result = collection.insert(data)
            collection.flush()
            logger.info(f"✅ Replaced records in {collection_name} with {len(data)} new records")
        else:
            logger.info(f"✅ Deleted records from {collection_name} (no new data provided)")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Error replacing data in {collection_name}: {e}")
        raise

def get_collection_info(collection_name: str) -> Dict[str, Any]:
    """
    Lấy thông tin về collection
    
    Args:
        collection_name: Tên collection
        
    Returns:
        Dictionary chứa thông tin collection
    """
    try:
        connect()
        collection = get_collection(collection_name)
        
        info = {
            "name": collection_name,
            "num_entities": collection.num_entities,
            "schema": {
                "fields": [
                    {
                        "name": field.name,
                        "dtype": str(field.dtype),
                        "is_primary": field.is_primary,
                        "auto_id": field.auto_id,
                        "max_length": field.max_length,
                        "dim": getattr(field, 'dim', None)
                    }
                    for field in collection.schema.fields
                ],
                "description": collection.schema.description,
                "enable_dynamic_field": collection.schema.enable_dynamic_field
            }
        }
        
        return info
        
    except Exception as e:
        logger.error(f"❌ Error getting collection info for {collection_name}: {e}")
        raise

def list_collections() -> List[str]:
    """
    Liệt kê tất cả collections
    
    Returns:
        List tên các collections
    """
    try:
        connect()
        collections = utility.list_collections()
        logger.info(f"✅ Found {len(collections)} collections")
        return collections
        
    except Exception as e:
        logger.error(f"❌ Error listing collections: {e}")
        raise

def drop_collection(collection_name: str) -> bool:
    """
    Xóa collection
    
    Args:
        collection_name: Tên collection cần xóa
        
    Returns:
        True nếu thành công
    """
    try:
        connect()
        if not utility.has_collection(collection_name):
            logger.warning(f"Collection '{collection_name}' does not exist")
            return False
        
        utility.drop_collection(collection_name)
        logger.info(f"✅ Dropped collection: {collection_name}")
        return True
        
    except Exception as e:
        logger.error(f"❌ Error dropping collection {collection_name}: {e}")
        raise

def create_collection(collection_name: str, 
                     fields: List[Dict[str, Any]], 
                     description: str = "",
                     enable_dynamic_field: bool = False) -> bool:
    """
    Tạo collection mới với schema được chỉ định
    
    Args:
        collection_name: Tên collection
        fields: Danh sách các field definitions
        description: Mô tả collection
        enable_dynamic_field: Cho phép dynamic fields
        
    Returns:
        True nếu thành công
    """
    try:
        connect()
        
        # Kiểm tra collection đã tồn tại
        if utility.has_collection(collection_name):
            logger.warning(f"Collection '{collection_name}' already exists")
            return True
        
        # Tạo fields từ config
        field_schemas = []
        for field_conf in fields:
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
            
            field_schemas.append(field)
        
        # Tạo schema và collection
        schema = CollectionSchema(fields=field_schemas, description=description, enable_dynamic_field=enable_dynamic_field)
        collection = Collection(collection_name, schema)
        
        # Tạo index cho vector fields
        vector_fields = [field for field in field_schemas if field.dtype == DataType.FLOAT_VECTOR]
        for vector_field in vector_fields:
            index_params = {
                "metric_type": "L2",
                "index_type": "IVF_FLAT",
                "params": {"nlist": 128}
            }
            collection.create_index(field_name=vector_field.name, index_params=index_params)
            logger.info(f"✅ Index created for field: {vector_field.name}")
        
        logger.info(f"✅ Collection '{collection_name}' created successfully")
        return True
        
    except Exception as e:
        logger.error(f"❌ Error creating collection {collection_name}: {e}")
        raise

