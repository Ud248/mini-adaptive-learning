# Database Setup và Management

Thư mục này chứa các script để setup và quản lý databases cho hệ thống học tập thích ứng.

## 📁 Cấu trúc thư mục

```
database/
├── mongodb/                    # MongoDB scripts
│   ├── setup_mongodb.py       # Setup database, collections, indexes
│   ├── insert_questions.py    # Import dữ liệu câu hỏi từ JSON
│   └── insert_teacher_books.py# Import dữ liệu SGV vào teacher_books
├── milvus/                    # Milvus scripts  
│   ├── setup_milvus.py        # Setup collections và indexes (bao gồm sgv_collection)
│   └── insert_sgv_to_milvus.py# Import dữ liệu SGV vào Milvus sgv_collection
├── data_insert/               # Dữ liệu để import
│   ├── grade1_math_questions_complete.json
│   └── sgv_ketnoitrithuc.json
└── README.md                 # Tài liệu này
```

## 🗄️ Databases được sử dụng

### 1. **MongoDB** - Primary Database
- **Mục đích**: Lưu trữ câu hỏi, kỹ năng, môn học
- **Collections**: placement_questions, skills, subjects, profile_student, teacher_books
- **Port**: 27017 (default)

### 2. **Milvus** - Vector Database  
- **Mục đích**: Lưu trữ embeddings và skill progress
- **Collections**: snapshot_student, skill_progress_collection, baitap_collection, sgv_collection
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
DATABASE_NAME=mini_adaptive_learning

# Milvus
MILVUS_HOST=localhost
MILVUS_PORT=19530
```

### 3. Setup MongoDB
```bash
cd mongodb
python setup_mongodb.py
python insert_questions.py
# Insert SGV (teacher_books)
python insert_teacher_books.py --grade 1 --subject "Toán" --year 2024 --curriculum "Kết nối tri thức"
# hoặc chỉ định JSON
$env:SGV_JSON_PATH="C:\\path\\to\\sgv_ketnoitrithuc.json"; python insert_teacher_books.py --grade 1 --subject "Toán"
```

### 4. Setup Milvus
```bash
cd milvus
python setup_milvus.py
# Insert SGV vào Milvus sgv_collection
python insert_sgv_to_milvus.py
# hoặc chỉ định JSON khác
$env:SGV_JSON_PATH="C:\\path\\to\\sgv_ketnoitrithuc.json"; python insert_sgv_to_milvus.py
```

## 📊 MongoDB Schema

### Collection: placement_questions
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

### Collection: profile_student
```javascript
{
  _id: ObjectId,
  student_email: "student1@gmail.com",
  username: "student1",
  low_accuracy_skills: ["S01", "S03"],
  slow_response_skills: ["S02"],
  created_at: ISODate,
  updated_at: ISODate,
  status: "active"
}
```

### Collection: teacher_books
```javascript
{
  _id: ObjectId|string,
  grade: 1,
  subject: "Toán",
  lesson: "CÁC SỐ 0, 1, 2, 3, 4, 5",
  parts: [
    { topic: "I MỤC TIÊU", content: "..." },
    { topic: "II HOẠT ĐỘNG", content: ["...", "..."] }
  ],
  info: { page: 12, source: "SGV Toán 1 - KNTT (ISBN ...)" },
  metadata: { curriculum: "Kết nối tri thức", book_type: "SGV", year: 2024, tags: ["Toán", "Grade 1", "Kết nối tri thức"] },
  created_at: ISODate,
  updated_at: ISODate
}
```
Indexes: `grade`, `subject`, `lesson`, `metadata.tags` (được tạo trong `insert_teacher_books.py`).

## 🔍 Milvus Schema

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

### Collection: sgv_collection
- **id** (INT64, PK, auto_id)
- **lesson** (VARCHAR, max_length=2048)
- **content** (VARCHAR, max_length=65535)
- **source** (VARCHAR, max_length=2048)
- **embedding** (FLOAT_VECTOR, 768D)
Description: SGV content with topic and embeddings. `enable_dynamic_field=true`.

## 🔧 Usage Examples

### MongoDB Queries
```python
# Tìm câu hỏi theo skill
questions = db.placement_questions.find({"skill": "S1", "grade": 1})

# Tạo quiz ngẫu nhiên
pipeline = [
    {"$match": {"grade": 1, "subject": "Toán"}},
    {"$sample": {"size": 30}}
]
quiz_questions = list(db.placement_questions.aggregate(pipeline))
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

### Insert SGV vào Milvus (ví dụ)
```bash
python database/milvus/insert_sgv_to_milvus.py
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

### Path import khi chạy script trực tiếp
- Nếu gặp `ModuleNotFoundError: database` khi chạy script trong thư mục con, hãy chạy từ project root hoặc dùng đường dẫn đầy đủ. Script `insert_sgv_to_milvus.py` đã tự thêm project root vào `sys.path`.

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
mongodump --db mini_adaptive_learning --out backup/

# MongoDB restore  
mongorestore --db mini_adaptive_learning backup/mini_adaptive_learning/
```

Database setup hoàn tất! 🎉
