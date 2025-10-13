#!/usr/bin/env python3
"""
MongoDB Client - Thư viện CRUD cho MongoDB Database
==================================================

File này cung cấp các hàm CRUD cơ bản để tương tác với MongoDB collections.
Được thiết kế để các module khác có thể import và sử dụng.

Chức năng chính:
- Kết nối và quản lý kết nối MongoDB
- Thao tác CRUD cơ bản: insert, update, delete, find, aggregate
- Tạo và quản lý collections và indexes
- Tìm kiếm và query dữ liệu với filter phức tạp

Các hàm CRUD:
- insert(): Thêm dữ liệu mới (insertOne hoặc insertMany)
- update(): Cập nhật documents hiện có
- delete(): Xóa documents dựa trên filter
- find(): Tìm kiếm documents với filter
- aggregate(): Thực hiện aggregation pipeline
- create_index(): Tạo indexes cho collection
- get_collection_info(): Lấy thông tin collection
- list_collections(): Liệt kê tất cả collections
- drop_collection(): Xóa collection
"""

from pymongo import MongoClient, ASCENDING, DESCENDING, TEXT
from pymongo.collection import Collection
from pymongo.database import Database
from pymongo.errors import DuplicateKeyError, OperationFailure
import os
from dotenv import load_dotenv
from typing import List, Dict, Any, Optional, Union
import logging
from datetime import datetime

load_dotenv()

MONGO_URL = os.getenv("MONGO_URL", "mongodb://localhost:27017")
DATABASE_NAME = os.getenv("DATABASE_NAME", "mini_adaptive_learning")

# Setup logging - Chỉ hiển thị ERROR và WARNING
logging.basicConfig(level=logging.WARNING)
logger = logging.getLogger(__name__)

def connect() -> Database:
    """Kết nối đến MongoDB và trả về database"""
    try:
        client = MongoClient(MONGO_URL)
        # Test connection
        client.admin.command('ping')
        db = client[DATABASE_NAME]
        logger.info(f"✅ Connected to MongoDB at {MONGO_URL}, database: {DATABASE_NAME}")
        return db
    except Exception as e:
        logger.error(f"❌ Error connecting to MongoDB: {e}")
        raise

def get_collection(collection_name: str) -> Collection:
    """Lấy collection từ database"""
    try:
        db = connect()
        collection = db[collection_name]
        return collection
    except Exception as e:
        logger.error(f"❌ Error getting collection {collection_name}: {e}")
        raise

def insert(collection_name: str, data: Union[Dict[str, Any], List[Dict[str, Any]]], 
          many: bool = False) -> Union[str, List[str]]:
    """
    Thêm dữ liệu vào collection
    
    Args:
        collection_name: Tên collection
        data: Document hoặc danh sách documents cần insert
        many: True nếu insert nhiều documents
        
    Returns:
        ID của document đã được insert (hoặc danh sách IDs)
    """
    try:
        collection = get_collection(collection_name)
        
        # Thêm timestamp nếu chưa có
        if isinstance(data, dict):
            if 'created_at' not in data:
                data['created_at'] = datetime.utcnow()
            if 'updated_at' not in data:
                data['updated_at'] = datetime.utcnow()
        elif isinstance(data, list):
            for doc in data:
                if 'created_at' not in doc:
                    doc['created_at'] = datetime.utcnow()
                if 'updated_at' not in doc:
                    doc['updated_at'] = datetime.utcnow()
        
        if many:
            result = collection.insert_many(data)
            logger.info(f"✅ Inserted {len(result.inserted_ids)} documents into {collection_name}")
            return [str(id) for id in result.inserted_ids]
        else:
            result = collection.insert_one(data)
            logger.info(f"✅ Inserted 1 document into {collection_name}")
            return str(result.inserted_id)
        
    except DuplicateKeyError as e:
        logger.error(f"❌ Duplicate key error in {collection_name}: {e}")
        raise
    except Exception as e:
        logger.error(f"❌ Error inserting data into {collection_name}: {e}")
        raise

def update(collection_name: str, filter_query: Dict[str, Any], 
          update_data: Dict[str, Any], many: bool = False, 
          upsert: bool = False) -> int:
    """
    Cập nhật documents trong collection
    
    Args:
        collection_name: Tên collection
        filter_query: Query để filter documents cần update
        update_data: Dữ liệu cần update
        many: True nếu update nhiều documents
        upsert: True nếu tạo document mới nếu không tìm thấy
        
    Returns:
        Số lượng documents đã được update
    """
    try:
        collection = get_collection(collection_name)
        
        # Thêm updated_at
        if '$set' in update_data:
            update_data['$set']['updated_at'] = datetime.utcnow()
        else:
            update_data['$set'] = {'updated_at': datetime.utcnow()}
        
        if many:
            result = collection.update_many(filter_query, update_data, upsert=upsert)
            logger.info(f"✅ Updated {result.modified_count} documents in {collection_name}")
            return result.modified_count
        else:
            result = collection.update_one(filter_query, update_data, upsert=upsert)
            logger.info(f"✅ Updated {result.modified_count} document in {collection_name}")
            return result.modified_count
        
    except Exception as e:
        logger.error(f"❌ Error updating data in {collection_name}: {e}")
        raise

def delete(collection_name: str, filter_query: Dict[str, Any], 
          many: bool = False) -> int:
    """
    Xóa documents từ collection
    
    Args:
        collection_name: Tên collection
        filter_query: Query để filter documents cần xóa
        many: True nếu xóa nhiều documents
        
    Returns:
        Số lượng documents đã được xóa
    """
    try:
        collection = get_collection(collection_name)
        
        if many:
            result = collection.delete_many(filter_query)
            logger.info(f"✅ Deleted {result.deleted_count} documents from {collection_name}")
            return result.deleted_count
        else:
            result = collection.delete_one(filter_query)
            logger.info(f"✅ Deleted {result.deleted_count} document from {collection_name}")
            return result.deleted_count
        
    except Exception as e:
        logger.error(f"❌ Error deleting data from {collection_name}: {e}")
        raise

def find(collection_name: str, filter_query: Dict[str, Any] = None, 
         projection: Dict[str, Any] = None, sort: List[tuple] = None, 
         limit: int = None, skip: int = None) -> List[Dict[str, Any]]:
    """
    Tìm kiếm documents trong collection
    
    Args:
        collection_name: Tên collection
        filter_query: Query để filter documents
        projection: Các fields cần trả về
        sort: Sắp xếp kết quả
        limit: Giới hạn số lượng kết quả
        skip: Bỏ qua số lượng documents
        
    Returns:
        Danh sách documents tìm được
    """
    try:
        collection = get_collection(collection_name)
        
        # Xây dựng query
        query = collection.find(filter_query or {})
        
        if projection:
            query = query.projection(projection)
        
        if sort:
            query = query.sort(sort)
        
        if skip:
            query = query.skip(skip)
        
        if limit:
            query = query.limit(limit)
        
        results = list(query)
        logger.info(f"✅ Found {len(results)} documents in {collection_name}")
        return results
        
    except Exception as e:
        logger.error(f"❌ Error finding data in {collection_name}: {e}")
        raise

def find_one(collection_name: str, filter_query: Dict[str, Any] = None, 
             projection: Dict[str, Any] = None) -> Optional[Dict[str, Any]]:
    """
    Tìm kiếm một document trong collection
    
    Args:
        collection_name: Tên collection
        filter_query: Query để filter document
        projection: Các fields cần trả về
        
    Returns:
        Document tìm được hoặc None
    """
    try:
        collection = get_collection(collection_name)
        
        query = collection.find_one(filter_query or {})
        if projection:
            query = collection.find_one(filter_query or {}, projection)
        
        if query:
            logger.info(f"✅ Found 1 document in {collection_name}")
        else:
            logger.info(f"ℹ️ No document found in {collection_name}")
        
        return query
        
    except Exception as e:
        logger.error(f"❌ Error finding one document in {collection_name}: {e}")
        raise

def aggregate(collection_name: str, pipeline: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Thực hiện aggregation pipeline
    
    Args:
        collection_name: Tên collection
        pipeline: Aggregation pipeline
        
    Returns:
        Kết quả aggregation
    """
    try:
        collection = get_collection(collection_name)
        results = list(collection.aggregate(pipeline))
        logger.info(f"✅ Aggregation completed in {collection_name}, returned {len(results)} results")
        return results
        
    except Exception as e:
        logger.error(f"❌ Error aggregating data in {collection_name}: {e}")
        raise

def create_index(collection_name: str, index_spec: Union[str, List[tuple], Dict[str, Any]], 
                unique: bool = False, background: bool = True) -> str:
    """
    Tạo index cho collection
    
    Args:
        collection_name: Tên collection
        index_spec: Index specification
        unique: True nếu index là unique
        background: True nếu tạo index trong background
        
    Returns:
        Tên index đã tạo
    """
    try:
        collection = get_collection(collection_name)
        
        # Tạo index
        result = collection.create_index(
            index_spec,
            unique=unique,
            background=background
        )
        
        logger.info(f"✅ Created index '{result}' for {collection_name}")
        return result
        
    except Exception as e:
        logger.error(f"❌ Error creating index for {collection_name}: {e}")
        raise

def create_text_index(collection_name: str, fields: List[str], 
                     language: str = "none") -> str:
    """
    Tạo text index cho collection
    
    Args:
        collection_name: Tên collection
        fields: Danh sách fields cần tạo text index
        language: Ngôn ngữ cho text index
        
    Returns:
        Tên index đã tạo
    """
    try:
        collection = get_collection(collection_name)
        
        # Tạo text index
        index_spec = [(field, TEXT) for field in fields]
        result = collection.create_index(
            index_spec,
            default_language=language
        )
        
        logger.info(f"✅ Created text index '{result}' for {collection_name}")
        return result
        
    except Exception as e:
        logger.error(f"❌ Error creating text index for {collection_name}: {e}")
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
        collection = get_collection(collection_name)
        
        # Lấy thông tin cơ bản
        stats = collection.database.command("collStats", collection_name)
        
        # Lấy danh sách indexes
        indexes = list(collection.list_indexes())
        
        info = {
            "name": collection_name,
            "count": collection.count_documents({}),
            "size": stats.get("size", 0),
            "avgObjSize": stats.get("avgObjSize", 0),
            "storageSize": stats.get("storageSize", 0),
            "indexes": [
                {
                    "name": idx["name"],
                    "key": idx["key"],
                    "unique": idx.get("unique", False),
                    "sparse": idx.get("sparse", False)
                }
                for idx in indexes
            ]
        }
        
        return info
        
    except Exception as e:
        logger.error(f"❌ Error getting collection info for {collection_name}: {e}")
        raise

def list_collections() -> List[str]:
    """
    Liệt kê tất cả collections
    
    Returns:
        Danh sách tên các collections
    """
    try:
        db = connect()
        collections = db.list_collection_names()
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
        collection = get_collection(collection_name)
        collection.drop()
        logger.info(f"✅ Dropped collection: {collection_name}")
        return True
        
    except Exception as e:
        logger.error(f"❌ Error dropping collection {collection_name}: {e}")
        raise

def count_documents(collection_name: str, filter_query: Dict[str, Any] = None) -> int:
    """
    Đếm số lượng documents trong collection
    
    Args:
        collection_name: Tên collection
        filter_query: Query để filter documents
        
    Returns:
        Số lượng documents
    """
    try:
        collection = get_collection(collection_name)
        count = collection.count_documents(filter_query or {})
        logger.info(f"✅ Counted {count} documents in {collection_name}")
        return count
        
    except Exception as e:
        logger.error(f"❌ Error counting documents in {collection_name}: {e}")
        raise

def distinct(collection_name: str, field: str, filter_query: Dict[str, Any] = None) -> List[Any]:
    """
    Lấy danh sách giá trị distinct của một field
    
    Args:
        collection_name: Tên collection
        field: Tên field cần lấy distinct values
        filter_query: Query để filter documents
        
    Returns:
        Danh sách giá trị distinct
    """
    try:
        collection = get_collection(collection_name)
        values = collection.distinct(field, filter_query or {})
        logger.info(f"✅ Found {len(values)} distinct values for field '{field}' in {collection_name}")
        return values
        
    except Exception as e:
        logger.error(f"❌ Error getting distinct values from {collection_name}: {e}")
        raise

def bulk_write(collection_name: str, operations: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Thực hiện bulk write operations
    
    Args:
        collection_name: Tên collection
        operations: Danh sách các operations
        
    Returns:
        Kết quả bulk write
    """
    try:
        from pymongo import InsertOne, UpdateOne, DeleteOne, ReplaceOne
        
        collection = get_collection(collection_name)
        
        # Chuyển đổi operations thành pymongo operations
        pymongo_ops = []
        for op in operations:
            op_type = op.get("operation")
            if op_type == "insertOne":
                pymongo_ops.append(InsertOne(op["document"]))
            elif op_type == "updateOne":
                pymongo_ops.append(UpdateOne(op["filter"], op["update"], upsert=op.get("upsert", False)))
            elif op_type == "replaceOne":
                pymongo_ops.append(ReplaceOne(op["filter"], op["replacement"], upsert=op.get("upsert", False)))
            elif op_type == "deleteOne":
                pymongo_ops.append(DeleteOne(op["filter"]))
        
        result = collection.bulk_write(pymongo_ops)
        
        logger.info(f"✅ Bulk write completed in {collection_name}: {result.inserted_count} inserted, {result.modified_count} modified, {result.deleted_count} deleted")
        return {
            "inserted_count": result.inserted_count,
            "modified_count": result.modified_count,
            "deleted_count": result.deleted_count,
            "upserted_count": result.upserted_count
        }
        
    except Exception as e:
        logger.error(f"❌ Error bulk writing to {collection_name}: {e}")
        raise
