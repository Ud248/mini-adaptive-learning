# Quiz API Module

## 📋 Tổng quan

**Quiz API** là module backend chịu trách nhiệm xử lý logic tạo bài kiểm tra và chấm điểm trong hệ thống học tập thích ứng. Module này cung cấp API để frontend có thể tạo quiz, nộp bài và nhận kết quả.

**Vai trò trong hệ thống:**
- Xử lý tạo bài kiểm tra ngẫu nhiên từ database câu hỏi
- Chấm điểm và trả về kết quả chi tiết
- Cung cấp metadata về môn học, lớp học, chương học
- Tích hợp với Saint Analysis module để phân tích học tập

## ⚙️ Yêu cầu

- Python 3.8+
- File dữ liệu `grade1_math_questions_complete.json` (từ thư mục gốc project)

## 🚀 Cài đặt

```bash
# Cài đặt dependencies
pip install -r requirements.txt

# Thiết lập dữ liệu
python setup_data.py

# Chạy server
python main.py
```

Server chạy tại: `http://localhost:8001`

## 🔧 Cấu hình

**Environment Variables (bắt buộc khi dùng MongoDB làm nguồn câu hỏi):**

```
# Kết nối MongoDB
MONGO_URL=mongodb://localhost:27017
DATABASE_NAME=quiz_system
QUESTIONS_COLLECTION=questions

# Auth (JWT)
JWT_SECRET_KEY=your-secret-here
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=60

# (Tùy chọn) Cấu hình CORS frontend
# Frontend mặc định chạy tại http://localhost:3001
```

Ghi chú:
- Nếu không cấu hình hoặc MongoDB không có dữ liệu, API sẽ fallback sang đọc file JSON cục bộ để không chặn môi trường dev.
- CORS mặc định cho phép từ `http://localhost:3001`. Có thể sửa trực tiếp trong `main.py`.

**Dependencies chính:**
- `fastapi==0.104.1` - Web framework
- `uvicorn==0.24.0` - ASGI server
- `pydantic==2.5.0` - Data validation
- `python-multipart==0.0.6` - Form data handling

## 📁 Cấu trúc module

```
backend/quiz_api/
├── main.py                    # FastAPI server chính
├── requirements.txt           # Dependencies
├── setup_data.py             # Script copy dữ liệu
├── collection_export.json    # Dữ liệu câu hỏi (auto-generated)
└── README.md                 # Tài liệu này
```

## 🔌 API Endpoints

### Core Endpoints
- `GET /` - Health check
- `POST /quiz/generate` - Tạo bài kiểm tra mới
- `POST /quiz/submit` - Nộp bài và chấm điểm

### Metadata Endpoints
- `GET /quiz/subjects` - Danh sách môn học
- `GET /quiz/grades` - Danh sách lớp học
- `GET /quiz/chapters/{subject}` - Danh sách chương theo môn

### Debug Endpoints
- `POST /quiz/debug-submit` - Debug submission data
- `POST /quiz/submit-simple` - Simple submit endpoint

### Auth Endpoints
- `POST /auth/login` — Đăng nhập, trả về `access_token`
  - Body: `{ "email_or_username": string, "password": string }`
- `POST /auth/logout` — Đăng xuất (stateless), client tự xóa token
- `GET /me` — Lấy thông tin người dùng từ JWT (yêu cầu header `Authorization: Bearer <token>`) 

## 🏃‍♂️ Chạy module

```bash
# Chạy development server
python main.py

# Hoặc với uvicorn
uvicorn main:app --host 0.0.0.0 --port 8001 --reload
```

### Khởi tạo dữ liệu và người dùng mẫu

```bash
# Tạo database, collections và indexes
python ../../database/mongodb/setup_mongodb.py

# Seed người dùng mẫu (mật khẩu đã băm)
python ../../database/mongodb/insert_users.py

# Tài khoản mẫu:
#   email: student1@example.com (hoặc username: student1)
#   password: Student@123
```

## 🔗 Tích hợp

**Kết nối với các module khác:**
- **Frontend**: Nhận requests từ React app tại `http://localhost:3001`
- **Saint Analysis**: Có thể tích hợp để phân tích kết quả học tập
- **Data Collection**: Sử dụng dữ liệu từ `grade1_math_questions_complete.json`

**Data Flow:**
1. Frontend gửi request tạo quiz → Quiz API
2. Quiz API tạo bài kiểm tra ngẫu nhiên → Trả về cho Frontend
3. Frontend gửi answers → Quiz API chấm điểm
4. Quiz API trả về kết quả → Frontend hiển thị

## 🧪 Test API

```bash
# Health check
curl http://localhost:8001/

# Tạo quiz
curl -X POST http://localhost:8001/quiz/generate \
  -H "Content-Type: application/json" \
  -d '{"grade": 1, "subject": "Toán", "num_questions": 5}'

# Nộp bài
curl -X POST http://localhost:8001/quiz/submit \
  -H "Content-Type: application/json" \
  -d '{"quiz_id": "quiz_123", "answers": {"q1": "A", "q2": "B"}}'
```

## 🐛 Troubleshooting

**Lỗi "Không tìm thấy dữ liệu câu hỏi":**
```bash
python setup_data.py
```

**Lỗi CORS:** Kiểm tra frontend chạy đúng port và cấu hình `allow_origins` trong `main.py`
