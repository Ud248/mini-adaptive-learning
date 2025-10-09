# Database Module

A comprehensive database management module for the Mini Adaptive Learning system, providing tools for setting up, managing, and populating both MongoDB and Milvus databases with educational content and user data.

## Overview

This module handles the complete database infrastructure for an adaptive learning platform, including:

- **MongoDB**: Primary database for storing questions, skills, subjects, users, and teacher materials
- **Milvus**: Vector database for storing embeddings and enabling semantic search capabilities
- **Data Processing**: Scripts for importing and transforming educational content
- **Embedding Generation**: Vietnamese text embedding service using sentence-transformers

## Installation

### Prerequisites

```bash
# Install required dependencies
pip install -r ../requirements.txt
```

### Dependencies

- `pymongo>=4.6.0` - MongoDB driver
- `pymilvus` - Milvus vector database client
- `sentence-transformers==5.1.1` - Text embedding models
- `torch` - Deep learning framework
- `numpy==1.26.4` - Numerical computing
- `scikit-learn==1.3.2` - Machine learning utilities
- `python-dotenv` - Environment variable management

## Quick Start

### 1. Environment Setup

Create a `.env` file in the project root:

```env
# MongoDB Configuration
MONGO_URL=mongodb://localhost:27017
DATABASE_NAME=mini_adaptive_learning

# Milvus Configuration
MILVUS_HOST=localhost
MILVUS_PORT=19530
```

### 2. Database Setup

```bash
# Setup MongoDB collections and indexes
cd mongodb
python setup_mongodb.py

# Setup Milvus collections
cd ../milvus
python setup_milvus.py
```

### 3. Data Import

```bash
# Import users
cd mongodb
python insert_users.py

# Import questions and educational content
python insert_questions.py
python insert_sgk_exercises.py
python insert_teacher_books.py

# Import vector embeddings
cd ../milvus
python insert_sgv_to_milvus.py
python insert_sgk_vectors_to_milvus.py
```

## Module Structure

```
database/
├── data_insert/           # Raw data files (JSON)
├── embeddings/           # Text embedding service
├── milvus/              # Milvus vector database scripts
├── mongodb/             # MongoDB scripts
└── README.md           # This documentation
```

## Core Components

### 1. MongoDB Management (`mongodb/`)

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
- `teacher_books` - Educational materials (SGV)

#### `insert_users.py`
Imports user accounts with secure password hashing.

```python
# Usage
python insert_users.py

# Features:
# - SHA-256 password hashing with salt
# - User validation and error handling
# - Automatic upsert (insert or update)
```

**Parameters:**
- `file_path`: Path to users JSON file (default: `../data_insert/users_sample.json`)
- `MONGO_URL`: MongoDB connection string
- `DATABASE_NAME`: Target database name

**Returns:**
- Success count of inserted/updated users
- Error messages for failed operations

#### `insert_questions.py`
Imports quiz questions from JSON format into MongoDB.

```python
# Usage
python insert_questions.py

# Features:
# - Question normalization and validation
# - Skill and subject extraction
# - Automatic ID generation
```

#### `insert_sgk_exercises.py`
Processes and imports textbook exercises with metadata.

```python
# Usage
python insert_sgk_exercises.py

# Environment variables:
# SGK_JSON_1: Path to first textbook JSON
# SGK_JSON_2: Path to second textbook JSON
```

#### `insert_teacher_books.py`
Imports teacher guide materials (SGV) with structured content.

```python
# Usage
python insert_teacher_books.py

# Environment variables:
# SGV_JSON_PATH: Path to SGV JSON file
# SGV_GRADE: Grade level (default: 1)
# SGV_SUBJECT: Subject name (default: "Toán")
# SGV_YEAR: Publication year (default: 2024)
```

### 2. Milvus Vector Database (`milvus/`)

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
Imports teacher guide content with vector embeddings.

```python
# Usage
python insert_sgv_to_milvus.py

# Features:
# - Automatic text preprocessing
# - Vietnamese embedding generation
# - Batch vector insertion
```

#### `insert_sgk_vectors_to_milvus.py`
Processes textbook exercises and creates vector embeddings.

```python
# Usage
python insert_sgk_vectors_to_milvus.py

# Features:
# - Text normalization for Vietnamese content
# - Multi-field embedding (question + lesson + subject)
# - Vector dimension: 768D
```

### 3. Embedding Service (`embeddings/`)

#### `local_embedder.py`
High-performance Vietnamese text embedding service.

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

# Embed multiple texts
texts = ["Text 1", "Text 2", "Text 3"]
embeddings = embedder.embed_texts(texts)

# Parallel processing for large datasets
large_embeddings = embedder.embed_texts_parallel(texts, max_workers=2)
```

**Key Features:**
- **GPU/CPU Detection**: Automatic device selection
- **Memory Management**: Handles large datasets efficiently
- **Batch Processing**: Optimized for vector database insertion
- **Error Recovery**: Retry logic for failed operations
- **Progress Tracking**: Real-time processing status

**Parameters:**
- `model_name` (str): HuggingFace model identifier
- `batch_size` (int): Processing batch size (default: 16)
- `verbose` (bool): Enable progress logging

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

### Milvus
- Load collections before querying
- Use appropriate index types (IVF_FLAT, IVF_SQ8)
- Batch insert operations for better throughput

### Embedding Service
- Use GPU when available for faster processing
- Adjust batch size based on available memory
- Use parallel processing for large datasets

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

## Troubleshooting

### Installation Issues
- Ensure Python 3.8+ is installed
- Install dependencies in correct order
- Check for version conflicts in requirements.txt

### Database Connection Issues
- Verify database services are running
- Check firewall and network connectivity
- Validate connection strings and credentials

### Performance Issues
- Monitor memory usage during embedding generation
- Optimize batch sizes for your hardware
- Use appropriate database indexes

For additional support, refer to the individual script documentation or check the project's main README file.