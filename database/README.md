# Database Setup và Management

Thư mục này chứa các script để setup và quản lý databases cho hệ thống học tập thích ứng.

## 📁 Cấu trúc thư mục

```
database/
├── mongodb/                    # MongoDB scripts
│   ├── setup_mongodb.py       # Setup database, collections, indexes
│   └── insert_questions.py    # Import dữ liệu từ JSON
├── milvus/                    # Milvus scripts  
│   └── setup_milvus.py       # Setup collections và indexes
├── data_insert/               # Dữ liệu để import
│   └── grade1_math_questions_complete.json
└── README.md                 # Tài liệu này
```

## 🗄️ Databases được sử dụng

### 1. **MongoDB** - Primary Database
- **Mục đích**: Lưu trữ câu hỏi, kỹ năng, môn học
- **Collections**: questions, skills, subjects, quiz_sessions
- **Port**: 27017 (default)

### 2. **Milvus** - Vector Database  
- **Mục đích**: Lưu trữ embeddings và profiles học sinh
- **Collections**: profile_student, snapshot_student, skill_progress_collection
- **Port**: 19530 (default)

## 🚀 Setup Instructions

### 1. Cài đặt dependencies
```bash
# Cài đặt từ requirements.txt ở project root
pip install -r ../requirements.txt
```

### 2. Cấu hình environment
Tạo file `.env`:
```env
# MongoDB
MONGO_URL=mongodb://localhost:27017
DATABASE_NAME=quiz_system

# Milvus
MILVUS_HOST=localhost
MILVUS_PORT=19530
```

### 3. Setup MongoDB
```bash
cd mongodb
python setup_mongodb.py
python insert_questions.py
```

### 4. Setup Milvus
```bash
cd milvus
python setup_milvus.py
```

## 📊 MongoDB Schema

### Collection: questions
```javascript
{
  _id: ObjectId,
  question_id: "Q00001",
  grade: 1,
  skill: "S1",
  skill_name: "Các số 0, 1, 2, 3, 4, 5",
  subject: "Toán",
  question: "Số nào đứng trước số 3?",
  image_question: "",
  answers: [
    {text: "2", correct: true},
    {text: "1", correct: false}
  ],
  image_answer: "",
  difficulty: "easy",
  created_at: ISODate,
  updated_at: ISODate
}
```

### Collection: skills
```javascript
{
  _id: ObjectId,
  skill_id: "S1",
  skill_name: "Các số 0, 1, 2, 3, 4, 5",
  grade: 1,
  subject: "Toán",
  created_at: ISODate,
  updated_at: ISODate
}
```

### Collection: subjects
```javascript
{
  _id: ObjectId,
  subject_id: "Toán_1",
  subject_name: "Toán",
  grade: 1,
  created_at: ISODate,
  updated_at: ISODate
}
```

## 🔍 Milvus Schema

### Collection: profile_student
- **student_id** (VARCHAR, PK)
- **low_accuracy_skills** (VARCHAR)
- **slow_response_skills** (VARCHAR)  
- **embedding_vector** (FLOAT_VECTOR, 128D)

### Collection: snapshot_student
- **id** (INT64, PK)
- **student_id** (VARCHAR)
- **timestamp** (VARCHAR)
- **low_accuracy_skills** (VARCHAR)
- **slow_response_skills** (VARCHAR)
- **embedding_vector** (FLOAT_VECTOR, 128D)

### Collection: skill_progress_collection
- **id** (INT64, PK)
- **student_id** (VARCHAR)
- **skill_id** (VARCHAR)
- **timestamp** (VARCHAR)
- **accuracy** (FLOAT)
- **avg_time** (FLOAT)
- **progress_vector** (FLOAT_VECTOR, 64D)

## 🔧 Usage Examples

### MongoDB Queries
```python
# Tìm câu hỏi theo skill
questions = db.questions.find({"skill": "S1", "grade": 1})

# Tạo quiz ngẫu nhiên
pipeline = [
    {"$match": {"grade": 1, "subject": "Toán"}},
    {"$sample": {"size": 30}}
]
quiz_questions = list(db.questions.aggregate(pipeline))
```

### Milvus Queries
```python
# Tìm học sinh tương tự
results = collection.search(
    data=[embedding_vector],
    anns_field="embedding_vector",
    param={"metric_type": "L2", "params": {"nprobe": 10}},
    limit=5
)
```

## 🐛 Troubleshooting

### MongoDB Issues
- **Connection refused**: Kiểm tra MongoDB service đang chạy
- **Authentication failed**: Kiểm tra username/password
- **Index creation failed**: Kiểm tra quyền write

### Milvus Issues  
- **Connection refused**: Kiểm tra Milvus service đang chạy
- **Collection exists**: Sử dụng `utility.has_collection()` để kiểm tra
- **Index creation failed**: Kiểm tra vector dimension

## 📈 Performance Tips

### MongoDB
- Tạo compound indexes cho queries thường dùng
- Sử dụng projection để giảm data transfer
- Implement connection pooling

### Milvus
- Load collections trước khi query
- Sử dụng appropriate index type (IVF_FLAT, IVF_SQ8)
- Batch insert operations

## 🔄 Data Migration

### From JSON to MongoDB
```bash
cd mongodb
python insert_questions.py
```

### Backup & Restore
```bash
# MongoDB backup
mongodump --db quiz_system --out backup/

# MongoDB restore  
mongorestore --db quiz_system backup/quiz_system/
```

Database setup hoàn tất! 🎉
