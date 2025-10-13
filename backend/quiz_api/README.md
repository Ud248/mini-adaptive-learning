# Quiz API Module

## 📋 Tổng quan

**Quiz API** là backend dịch vụ tạo bài kiểm tra, chấm điểm và cung cấp metadata cho hệ thống học tập thích ứng. Frontend giao tiếp với API này để tạo quiz, nộp bài và đọc thông tin liên quan.

**Vai trò trong hệ thống:**
- Tạo bài kiểm tra ngẫu nhiên từ MongoDB (fallback JSON cho môi trường dev)
- Chấm điểm và trả về kết quả (đầy đủ và phiên bản nhanh)
- Cung cấp metadata: môn, khối lớp, chương
- Tích hợp gửi log đến SAINT service

## ⚙️ Yêu cầu

- Python 3.8+
- (Tùy chọn dev) File `grade1_math_questions_complete.json` đặt tại `database/data_insert/grade1_math_questions_complete.json` (API đã tự tìm đường dẫn này; vẫn hỗ trợ fallback tại thư mục gốc project nếu cần)

## 🚀 Cài đặt

```bash
# Chạy server (dev)
python main.py

# Hoặc với uvicorn (khuyến nghị)
uvicorn main:app --host 0.0.0.0 --port 8001 --reload
```

Server chạy tại: `http://localhost:8001`

## 🔧 Cấu hình

Environment Variables (đặt trong shell hoặc `.env`):

```
# MongoDB
MONGO_URL=mongodb://localhost:27017
DATABASE_NAME=mini_adaptive_learning
QUESTIONS_COLLECTION=placement_questions

# Auth (JWT)
JWT_SECRET_KEY=your-secret-here
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=60
```

Ghi chú:
- Nếu MongoDB không có dữ liệu, API sẽ fallback sang file JSON để không chặn dev.
- CORS cho phép origin `http://localhost:3001` (có thể chỉnh trong `main.py`).

## 📁 Cấu trúc module

```
backend/quiz_api/
├── main.py                  # FastAPI server chính
├── requirements.txt         # Dependencies
└── README.md                # Tài liệu này
```

## 🔌 API Endpoints

### Core Endpoints
- `GET /` — Health check
- `POST /quiz/generate` — Tạo bài kiểm tra: gom skill theo `grade`/`subject`, lấy 2 câu/skill; fallback JSON nếu thiếu dữ liệu
- `POST /quiz/submit` — Nộp bài và chấm điểm (trả về chi tiết từng câu)

### Metadata Endpoints (đã gỡ khỏi phiên bản này)
- Đã gỡ: `GET /quiz/subjects`, `GET /quiz/grades`, `GET /quiz/chapters/{subject}`
  - Frontend đang dùng mặc định: Lớp 1, Môn Toán; thay đổi Lớp/Môn sẽ phát triển sau.

### Analysis / Integration
- `POST /quiz/submit-saint-data` — Nhận logs và chuyển tiếp đến SAINT API thực

### Profile / Skills
- `GET /quiz/weak-skills/{student_email}` — Lấy danh sách kỹ năng yếu của học sinh từ `profile_student`, enrich từ bảng `skills`
- `GET /api/users/name` — Lấy tên/username/email từ MongoDB (yêu cầu JWT qua header `Authorization: Bearer ...`)

### Auth
- `POST /auth/login` — Đăng nhập, trả `access_token`
  - Body: `{ "email_or_username": string, "password": string }`
- `POST /auth/logout` — Đăng xuất (stateless; client tự xóa token)

Đã gỡ: `GET /me`

## 🧪 Ví dụ gọi API

```bash
# Health check
curl http://localhost:8001/

# Tạo quiz (ví dụ lớp 1, Toán, 6 câu)
curl -X POST http://localhost:8001/quiz/generate \
  -H "Content-Type: application/json" \
  -d '{"grade": 1, "subject": "Toán", "num_questions": 6}'

# Nộp bài đầy đủ (chi tiết từng câu)
curl -X POST http://localhost:8001/quiz/submit \
  -H "Content-Type: application/json" \
  -d '{"quiz_id": "quiz_123", "answers": {"q1": "A", "q2": "B"}}'

# Yêu cầu tên người dùng (JWT)
curl -H "Authorization: Bearer <token>" http://localhost:8001/api/users/name
```

## 🔗 Data Flow

1) Frontend yêu cầu tạo quiz → API truy vấn MongoDB (mỗi skill 2 câu) → trả về danh sách câu hỏi đã chuẩn hóa.

2) Frontend gửi answers → API chấm điểm đơn giản → trả về tổng, số đúng, điểm, và chi tiết từng câu.

3) Logs (tuỳ chọn) gửi qua endpoint SAINT để phân tích nâng cao.

## 🐛 Troubleshooting

- "Không tìm thấy dữ liệu câu hỏi": kiểm tra MongoDB và fallback JSON; đảm bảo file `database/data_insert/grade1_math_questions_complete.json` có mặt (hoặc bản sao ở thư mục gốc project).
- CORS: kiểm tra `allow_origins` trong `main.py` phù hợp frontend.
