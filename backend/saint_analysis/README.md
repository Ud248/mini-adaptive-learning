## SAINT Analysis Backend

Lưu ý quan trọng: Đây là module GIẢ LẬP (simulator/stub) cho SAINT++. Khi có mô hình chính thức, sẽ tích hợp vào module này để thay thế logic mô phỏng hiện tại.

Hiện tại, chỉ sử dụng endpoint duy nhất: `/interaction` để nhận logs tương tác và sinh/ghi `profile_student` vào MongoDB, phục vụ các module phía sau (quiz, phân tích kỹ năng,...). Các endpoint khác là minh họa và có thể thay đổi khi tích hợp model thật.

### Cấu trúc ngắn gọn
```
backend/saint_analysis/
├── app/api/saint_api.py      # FastAPI endpoints (dùng /interaction)
├── app/services/*            # progress tracker, milvus/mongo helpers
├── main.py                   # entrypoint FastAPI
└── README.md
```

### Chạy nhanh
- Local (từ project root):
```bash
pip install -r backend/saint_analysis/requirements.txt
uvicorn backend.saint_analysis.main:app --host 0.0.0.0 --port 8000 --reload
```

### Cấu hình ngắn gọn
- Yêu cầu MongoDB (để lưu `profile_student`). Milvus là tùy chọn trong giai đoạn giả lập.
- Biến môi trường tối thiểu: kết nối MongoDB nếu cần tùy chỉnh.

### Endpoint trọng tâm: `/interaction`
- `POST /interaction`
- Mục đích: Nhận danh sách logs tương tác, cập nhật và ghi `profile_student` vào MongoDB để các module khác sử dụng.
- Ví dụ:
```bash
curl -X POST "http://localhost:8000/interaction" \
  -H "Content-Type: application/json" \
  -d '[{"student_id":"HS001","timestamp":"2024-01-01T10:00:00Z","question_text":"2+2?","answer":"4","skill_id":"S01","correct":true,"response_time":2.5}]'
```

### Database
- MongoDB: bắt buộc để lưu `profile_student` (đọc/ghi từ các module khác).
- Milvus: tùy chọn trong giai đoạn giả lập; sẽ dùng nhiều hơn khi tích hợp model thật.

### Test nhanh
```bash
curl -X GET "http://localhost:8000/"
curl -X POST "http://localhost:8000/interaction" -H "Content-Type: application/json" -d '[{"student_id":"HS001", "timestamp":"2025-01-01T00:00:00Z", "question_text":"2+3?", "answer":"5", "skill_id":"S01", "correct":true, "response_time":2.1}]'
```

### Ghi chú tích hợp model thật
- Khi có model chính thức: thay thế logic mô phỏng trong `app/api/saint_api.py` và mở rộng docs các endpoint khác (analyze, progress, trends, ...). Cấu trúc dữ liệu `profile_student` sẽ được giữ ổn định để không ảnh hưởng các module downstream.

### Khác (ngắn gọn)
- Health: `GET /` trả trạng thái chạy.
- Dev: `uvicorn backend.saint_analysis.main:app --reload`
- Prod: `uvicorn backend.saint_analysis.main:app --host 0.0.0.0 --port 8000 --workers 4`


