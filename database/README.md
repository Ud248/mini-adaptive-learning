# 🗄️ Database Module

> Comprehensive database management cho hệ thống Mini Adaptive Learning - Quản lý MongoDB, Milvus vector DB, và Vietnamese text embeddings

## 📋 Giới thiệu

Module **database** là lớp dữ liệu của hệ thống, đảm nhận:

- 📚 **MongoDB**: Primary database cho questions, users, skills, SGK/SGV content
- 🔍 **Milvus**: Vector database cho semantic search và RAG
- 🤖 **Vietnamese Embeddings**: Text embedding service với sentence-transformers
- ⚙️ **CRUD Clients**: Unified clients với error handling và logging
- 📊 **Data Import Scripts**: Import tools với progress bars và validation

## 🛠️ Tech Stack

```python
# Core
pymongo >= 4.6.0              # MongoDB driver
pymilvus                      # Milvus vector database
sentence-transformers==5.1.1  # Vietnamese embeddings
torch                         # Deep learning backend

# Utils
python-dotenv                 # Environment management
tqdm                          # Progress bars
numpy==1.26.4                # Numerical computing
scikit-learn==1.3.2          # ML utilities
```

## 📦 Cài đặt

```bash
# From project root
pip install -r requirements.txt
```

## 🚀 Quick Start

### 1. Environment Setup

Tạo file `.env` ở project root:

```env
# MongoDB
MONGO_URL=mongodb://localhost:27017
DATABASE_NAME=mini_adaptive_learning

# Milvus
MILVUS_HOST=localhost
MILVUS_PORT=19530

# Data paths
SGK_JSON_1=database/data_insert/sgk-toan-1-ket-noi-tri-thuc-tap-1.json
SGK_JSON_2=database/data_insert/sgk-toan-1-ket-noi-tri-thuc-tap-2.json
SGV_JSON_PATH=database/data_insert/sgv_ketnoitrithuc.json
```

### 2. Start Databases

```bash
# Via Docker Compose (recommended)
docker-compose up -d

# Or manual start
# MongoDB: mongod --dbpath /data/db
# Milvus: Follow Milvus installation guide
```

### 3. Setup Collections & Indexes

```bash
# MongoDB
cd database/mongodb
python setup_mongodb.py

# Milvus
cd ../milvus
python setup_milvus.py
```

### 4. Import Data

```bash
# MongoDB data (with progress bars)
cd database/mongodb
python insert_users.py                    # Import users
python insert_placement_questions.py      # Import quiz questions
python insert_sgk_to_mongodb.py          # Import textbook content
python insert_sgv_to_mongodb.py          # Import teacher guide

# Milvus vectors (with progress bars)
cd ../milvus
python insert_sgv_to_milvus.py           # Generate & insert SGV embeddings
python insert_sgk_to_milvus.py           # Generate & insert SGK embeddings
```

**✨ All scripts có progress bars và minimal logging!**

## 📁 Cấu trúc Module

```
database/
├── data_insert/                 # 📂 Raw JSON data files
│   ├── grade1_math_questions_complete.json
│   ├── sgk-toan-1-ket-noi-tri-thuc-tap-1.json
│   ├── sgk-toan-1-ket-noi-tri-thuc-tap-2.json
│   ├── sgv_ketnoitrithuc.json
│   └── users_sample.json
│
├── embeddings/                  # 🤖 Vietnamese embedding service
│   ├── local_embedder.py       # Main embedding class
│   └── __pycache__/
│
├── milvus/                      # 🔍 Vector database
│   ├── milvus_client.py        # CRUD client
│   ├── setup_milvus.py         # Create collections
│   ├── insert_sgv_to_milvus.py # Import teacher guide vectors
│   ├── insert_sgk_to_milvus.py # Import textbook vectors
│   └── __pycache__/
│
├── mongodb/                     # 📚 Primary database
│   ├── mongodb_client.py       # CRUD client
│   ├── setup_mongodb.py        # Create collections & indexes
│   ├── insert_users.py         # Import users
│   ├── insert_placement_questions.py  # Import quiz questions
│   ├── insert_sgk_to_mongodb.py       # Import textbook content
│   ├── insert_sgv_to_mongodb.py       # Import teacher guide
│   └── __pycache__/
│
└── README.md                    # 📖 This file
```

## Core Components

### 1. MongoDB Management (`mongodb/`)

#### `mongodb_client.py`
Unified CRUD client for MongoDB operations with automatic error handling and logging.

```python
from database.mongodb.mongodb_client import connect, insert, find, update, delete

# Connect to database
db = connect()

# Insert data
result = insert("collection_name", {"field": "value"})

# Find documents
docs = find("collection_name", {"field": "value"})

# Update documents
updated_count = update("collection_name", {"_id": "123"}, {"$set": {"field": "new_value"}})

# Delete documents
deleted_count = delete("collection_name", {"field": "value"})
```

**Key Features:**
- Automatic connection management
- Built-in error handling and logging
- Support for bulk operations
- Automatic timestamping (created_at, updated_at)
- Index management utilities

#### `setup_mongodb.py`
Creates database collections and indexes for optimal query performance.

```python
# Usage
python setup_mongodb.py
```

**Collections Created:**
- `placement_questions` - Quiz questions with answers
- `skills` - Learning skills and competencies
- `subjects` - Academic subjects
- `users` - User accounts and authentication
- `textbook_exercises` - Educational materials (SGK)
- `teacher_books` - Educational materials (SGV)

#### `insert_users.py`
Imports user accounts with secure password hashing and progress tracking.

```python
# Usage
python insert_users.py

# Features:
# - SHA-256 password hashing with salt
# - User validation and error handling
# - Automatic upsert (insert or update)
# - Progress bar for batch operations
# - Minimal logging output
```

**Output Example:**
```
Upserting users: 100%|██████████| 2/2 [00:00<00:00, 36.72user/s]
[SUCCESS] Processed 2 users: 2 new, 0 updated
```

#### `insert_placement_questions.py`
Imports quiz questions from JSON format into MongoDB with progress tracking.

```python
# Usage
python insert_placement_questions.py

# Features:
# - Question normalization and validation
# - Skill and subject extraction
# - Automatic ID generation
# - Progress bars for all operations
# - Upsert logic to prevent duplicates
```

**Progress Tracking:**
- Transforming questions: `tqdm` progress bar
- Inserting questions: Individual progress tracking
- Inserting skills: Progress tracking with upsert
- Inserting subjects: Progress tracking with upsert

#### `insert_sgk_to_mongodb.py`
Processes and imports textbook exercises with metadata and progress tracking.

```python
# Usage
python insert_sgk_to_mongodb.py

# Features:
# - Normalizes SGK data from multiple JSON files
# - Creates vector_id for Milvus integration
# - Progress bars for normalization and upsert
# - Automatic index creation (silent)
# - Upsert logic to prevent duplicates

# Environment variables:
# SGK_JSON_1: Path to first textbook JSON
# SGK_JSON_2: Path to second textbook JSON
```

**Output Example:**
```
Normalizing SGK items: 100%|██████████| 432/432 [00:00<00:00, 284672.32item/s]
Upserting SGK documents: 100%|██████████| 432/432 [00:18<00:00, 22.75doc/s]
[SUCCESS] Processed 432 docs: 0 new, 432 updated
```

#### `insert_sgv_to_mongodb.py`
Imports teacher guide materials (SGV) with structured content and progress tracking.

```python
# Usage
python insert_sgv_to_mongodb.py

# Features:
# - Processes SGV content with progress tracking
# - Automatic index creation
# - Batch insertion with progress display
# - Minimal logging output

# Environment variables:
# SGV_JSON_PATH: Path to SGV JSON file
# SGV_GRADE: Grade level (default: 1)
# SGV_SUBJECT: Subject name (default: "Toán")
# SGV_YEAR: Publication year (default: 2024)
```

### 2. Milvus Vector Database (`milvus/`)

#### `milvus_client.py`
Unified CRUD client for Milvus operations with automatic error handling and logging.

```python
from database.milvus.milvus_client import connect, insert, search, query, create_collection

# Connect to Milvus
client = connect()

# Create collection
create_collection("my_collection", fields, description="My collection")

# Insert vectors
result = insert("my_collection", data)

# Search similar vectors
results = search("my_collection", query_vectors, limit=10)

# Query with metadata filtering
results = query("my_collection", expr="field == 'value'")
```

**Key Features:**
- Automatic connection management
- Built-in error handling and logging
- Support for vector similarity search
- Metadata filtering capabilities
- Collection management utilities

#### `setup_milvus.py`
Creates vector database collections with proper schemas and indexes.

```python
# Usage
python setup_milvus.py

# Collections created:
# - snapshot_student: Student learning snapshots
# - skill_progress_collection: Skill progression tracking
# - baitap_collection: Exercise embeddings
# - sgv_collection: Teacher guide embeddings
```

#### `insert_sgv_to_milvus.py`
Imports teacher guide content with vector embeddings and progress tracking.

```python
# Usage
python insert_sgv_to_milvus.py

# Features:
# - Automatic text preprocessing
# - Vietnamese embedding generation
# - Batch vector insertion with progress bars
# - Minimal logging output
```

**Progress Tracking:**
- Processing items: `tqdm` progress bar
- Preparing texts: Progress tracking
- Preparing data: Progress tracking
- Inserting vectors: Batch progress display

#### `insert_sgk_to_milvus.py`
Processes textbook exercises and creates vector embeddings with progress tracking.

```python
# Usage
python insert_sgk_to_milvus.py

# Features:
# - Text normalization for Vietnamese content
# - Multi-field embedding (question + lesson + subject)
# - Vector dimension: 768D
# - Progress bars for all operations
# - Minimal logging output
```

**Progress Tracking:**
- Normalizing items: `tqdm` progress bar
- Building texts: Progress tracking
- Preparing data: Progress tracking
- Inserting vectors: Batch progress display

### 3. Embedding Service (`embeddings/`)

#### `local_embedder.py`
High-performance Vietnamese text embedding service with progress tracking.

```python
from database.embeddings.local_embedder import LocalEmbedding

# Initialize embedder
embedder = LocalEmbedding(
    model_name='dangvantuan/vietnamese-document-embedding',
    batch_size=16,
    verbose=True
)

# Embed single text
embedding = embedder.embed_single_text("Xin chào, tôi là trí tuệ nhân tạo.")

# Embed multiple texts with progress bar
texts = ["Text 1", "Text 2", "Text 3"]
embeddings = embedder.embed_texts(texts, show_progress=True)

# Parallel processing for large datasets with progress tracking
large_embeddings = embedder.embed_texts_parallel(texts, max_workers=2, show_progress=True)
```

**Key Features:**
- **GPU/CPU Detection**: Automatic device selection
- **Memory Management**: Handles large datasets efficiently
- **Batch Processing**: Optimized for vector database insertion
- **Error Recovery**: Retry logic for failed operations
- **Progress Tracking**: Real-time processing status with `tqdm` progress bars
- **Minimal Logging**: Clean output with progress bars only

**Progress Tracking:**
- `embed_texts()`: Progress bar for batch processing
- `embed_texts_parallel()`: Progress tracking for parallel operations
- `embed_chunks_for_database()`: Progress bar for database preparation
- `embed_texts_quick()`: Fast processing with progress display

**Parameters:**
- `model_name` (str): HuggingFace model identifier
- `batch_size` (int): Processing batch size (default: 16)
- `verbose` (bool): Enable progress logging
- `show_progress` (bool): Enable `tqdm` progress bars (default: True)

**Returns:**
- `List[List[float]]`: 768-dimensional embedding vectors
- `None`: For empty or invalid input

## Data Schemas

### MongoDB Collections

#### `placement_questions`
```javascript
{
  "_id": ObjectId,
  "question_id": "Q00001",
  "grade": 1,
  "skill": "S1",
  "skill_name": "Các số 0, 1, 2, 3, 4, 5",
  "subject": "Toán",
  "question": "Số nào đứng trước số 3?",
  "answers": [
    {"text": "2", "correct": true},
    {"text": "1", "correct": false}
  ],
  "image_question": "",
  "image_answer": "",
  "difficulty": "easy",
  "created_at": ISODate,
  "updated_at": ISODate
}
```

#### `users`
```javascript
{
  "_id": ObjectId,
  "email": "student1@gmail.com",
  "username": "student1",
  "role": "student",
  "full_name": "Phan Thiên Ân",
  "password_hash": "salt:hash",
  "created_at": ISODate,
  "updated_at": ISODate,
  "status": "active"
}
```

### Milvus Collections

#### `sgv_collection`
```python
{
  "id": INT64,           # Primary key (auto-generated)
  "lesson": VARCHAR,     # Lesson title (max 2048 chars)
  "content": VARCHAR,    # Full content (max 65535 chars)
  "source": VARCHAR,     # Source information (max 2048 chars)
  "embedding": FLOAT_VECTOR  # 768-dimensional vector
}
```

## Usage Examples

### Querying Questions by Skill

```python
from pymongo import MongoClient

client = MongoClient("mongodb://localhost:27017")
db = client["mini_adaptive_learning"]

# Find questions for specific skill
questions = db.placement_questions.find({
    "skill": "S1",
    "grade": 1,
    "subject": "Toán"
})

# Generate random quiz
pipeline = [
    {"$match": {"grade": 1, "subject": "Toán"}},
    {"$sample": {"size": 30}}
]
quiz_questions = list(db.placement_questions.aggregate(pipeline))
```

### Vector Similarity Search

```python
from pymilvus import Collection

# Load collection
collection = Collection("sgv_collection")
collection.load()

# Search for similar content
results = collection.search(
    data=[query_embedding],
    anns_field="embedding",
    param={"metric_type": "L2", "params": {"nprobe": 10}},
    limit=5,
    output_fields=["lesson", "content", "source"]
)
```

### Custom Embedding Generation

```python
from database.embeddings.local_embedder import LocalEmbedding

# Initialize with custom settings
embedder = LocalEmbedding(
    model_name='dangvantuan/vietnamese-document-embedding',
    batch_size=32,
    verbose=False
)

# Process educational content
content = "Bài học về phép cộng trong phạm vi 10"
embedding = embedder.embed_single_text(content)

# Batch processing for multiple documents
documents = [
    "Nội dung bài học 1",
    "Nội dung bài học 2",
    "Nội dung bài học 3"
]
embeddings = embedder.embed_texts(documents)
```

## Error Handling

### Common Issues

**MongoDB Connection Errors:**
```python
# Check MongoDB service status
from pymongo import MongoClient
try:
    client = MongoClient("mongodb://localhost:27017")
    client.admin.command('ping')
    print("MongoDB connection successful")
except Exception as e:
    print(f"MongoDB connection failed: {e}")
```

**Milvus Collection Errors:**
```python
from pymilvus import utility

# Check if collection exists
if utility.has_collection("sgv_collection"):
    print("Collection exists")
else:
    print("Collection not found - run setup_milvus.py")
```

**Embedding Generation Errors:**
```python
try:
    embedding = embedder.embed_single_text(text)
except ValueError as e:
    print(f"Embedding failed: {e}")
    # Handle empty or invalid text
```

## Performance Optimization

### MongoDB
- Use compound indexes for frequent query patterns
- Implement connection pooling for high-traffic applications
- Use projection to limit returned fields
- Leverage `mongodb_client.py` for optimized CRUD operations

### Milvus
- Load collections before querying
- Use appropriate index types (IVF_FLAT, IVF_SQ8)
- Batch insert operations for better throughput
- Leverage `milvus_client.py` for optimized vector operations

### Embedding Service
- Use GPU when available for faster processing
- Adjust batch size based on available memory
- Use parallel processing for large datasets
- Enable progress tracking for better user experience

### Progress Tracking
- All import scripts now feature `tqdm` progress bars
- Minimal logging output for cleaner console experience
- Real-time processing status and ETA estimates
- Batch operation progress tracking

## Data Migration

### Backup and Restore

```bash
# MongoDB backup
mongodump --db mini_adaptive_learning --out backup/

# MongoDB restore
mongorestore --db mini_adaptive_learning backup/mini_adaptive_learning/

# Milvus backup (requires Milvus backup tools)
# Refer to Milvus documentation for backup procedures
```

### Environment Migration

```bash
# Update connection strings in .env
MONGO_URL=mongodb://new-host:27017
MILVUS_HOST=new-milvus-host
MILVUS_PORT=19530
```

## 🐛 Troubleshooting

### 1. MongoDB Connection Failed

**Error**: `pymongo.errors.ServerSelectionTimeoutError`

```bash
# Check if MongoDB is running
docker ps | grep mongo
# Or
mongosh --eval "db.runCommand({ ping: 1 })"

# Restart MongoDB
docker-compose restart mongodb

# Check connection string
python -c "
from database.mongodb.mongodb_client import connect
db = connect()
print('✓ Connected:', db.name)
"
```

### 2. Milvus Connection Failed

**Error**: `MilvusException: failed to connect to server`

```bash
# Check Milvus status
docker ps | grep milvus

# Restart Milvus
docker-compose restart milvus-standalone

# Test connection
python -c "
from pymilvus import connections
connections.connect('default', host='localhost', port='19530')
print('✓ Connected to Milvus')
"
```

### 3. Empty Collections

**Issue**: Collections exist but have no data

```bash
# Check MongoDB
python -c "
from database.mongodb.mongodb_client import connect
db = connect()
print('placement_questions:', db.placement_questions.count_documents({}))
print('users:', db.users.count_documents({}))
print('textbook_exercises:', db.textbook_exercises.count_documents({}))
"

# Check Milvus
python -c "
from pymilvus import Collection
sgv = Collection('sgv_collection')
print('SGV vectors:', sgv.num_entities)
baitap = Collection('baitap_collection')
print('Baitap vectors:', baitap.num_entities)
"

# Re-import if needed
cd database/mongodb
python insert_placement_questions.py
```

### 4. Embedding Generation Slow/Failed

**Issue**: Embedding takes too long or OOM

```python
# Reduce batch size in local_embedder.py
embedder = LocalEmbedding(
    batch_size=8,  # Default: 16, reduce if OOM
    verbose=True
)

# Use CPU if GPU issues
import torch
torch.cuda.is_available()  # Should return False to force CPU
```

**Issue**: `CUDA out of memory`

```bash
# Clear GPU cache
python -c "
import torch
torch.cuda.empty_cache()
print('✓ GPU cache cleared')
"

# Or force CPU mode
export CUDA_VISIBLE_DEVICES=-1
```

### 5. Progress Bar Not Showing

**Issue**: No progress bars during import

```bash
# Install tqdm
pip install tqdm

# Check terminal encoding (Windows)
chcp 65001  # Set UTF-8 encoding

# Use PowerShell (better Unicode support)
# Not CMD
```

### 6. Duplicate Data Issues

**Issue**: Running import scripts multiple times creates duplicates

```bash
# Scripts use UPSERT logic - safe to re-run
# But if you want to clean:

# MongoDB - Drop collection
python -c "
from database.mongodb.mongodb_client import connect
db = connect()
db.placement_questions.drop()
print('✓ Dropped placement_questions')
"

# Milvus - Drop collection
python -c "
from pymilvus import utility
utility.drop_collection('sgv_collection')
print('✓ Dropped sgv_collection')
"

# Then re-setup and re-import
python setup_mongodb.py
python insert_placement_questions.py
```

### 7. Import Script Hangs

**Issue**: Script hangs without error

```bash
# Check file paths in .env
cat .env | grep JSON

# Verify JSON files exist
ls -la database/data_insert/*.json

# Check file permissions
# Windows: Right-click > Properties > Security

# Test JSON validity
python -c "
import json
with open('database/data_insert/grade1_math_questions_complete.json') as f:
    data = json.load(f)
    print(f'✓ Valid JSON: {len(data)} items')
"
```

### 8. Vector Search Returns Nothing

**Issue**: Milvus search returns empty results

```python
from pymilvus import Collection

# Load collection first (important!)
collection = Collection('sgv_collection')
collection.load()

# Check if collection has data
print(f"Entities: {collection.num_entities}")

# Verify embedding dimension matches (768)
print(f"Schema: {collection.schema}")
```

### 9. Slow Vector Search

**Issue**: Milvus search takes too long

```python
# Create index if not exists
from pymilvus import Collection

collection = Collection('sgv_collection')

# Check current index
print(collection.index().params)

# Create IVF_FLAT index
index_params = {
    "metric_type": "L2",
    "index_type": "IVF_FLAT",
    "params": {"nlist": 128}
}
collection.create_index("embedding", index_params)
collection.load()
```

### 10. Docker Issues

**Issue**: Containers won't start

```bash
# Check Docker is running
docker info

# Check disk space
df -h

# View logs
docker-compose logs milvus-standalone
docker-compose logs mongodb

# Restart all
docker-compose down
docker-compose up -d

# Check ports not in use
netstat -an | findstr :19530  # Milvus
netstat -an | findstr :27017  # MongoDB
```

---

## 📚 Tài liệu tham khảo

- [MongoDB Python Driver Docs](https://pymongo.readthedocs.io/)
- [Milvus Python SDK Docs](https://milvus.io/docs)
- [Sentence Transformers Docs](https://www.sbert.net/)
- [Vietnamese Embedding Model](https://huggingface.co/dangvantuan/vietnamese-document-embedding)

---

**Maintainer**: Mini Adaptive Learning Team  
**Last Updated**: October 17, 2025