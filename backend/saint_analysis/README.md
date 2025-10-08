## SAINT Analysis Backend

Hệ thống phân tích năng lực học sinh dựa trên mô hình SAINT++ với API FastAPI và lưu trữ hồ sơ/vector trong Milvus. Tài liệu này hợp nhất hướng dẫn test API, yêu cầu cơ sở dữ liệu Milvus, định dạng input/output và quy trình vận hành.

### 1) Cấu trúc thư mục
```
backend/saint_analysis/
├── app/
│   ├── api/saint_api.py            # FastAPI endpoints
│   ├── core/*                      # utils, singleton
│   ├── dataset/saint_dataset.py    # dataset helpers
│   ├── model/*                     # SAINT / train / evaluate / updater
│   └── services/*                  # milvus client, progress tracker
├── data/                           # dữ liệu ví dụ + script tạo data
├── output/                         # model weights & ánh xạ id
├── demo_gradio.py                  # demo suy luận local
├── milvus_api.py                   # (tuỳ chọn) API nội bộ thao tác Milvus
├── main.py                         # entrypoint FastAPI (module backend.saint_analysis.main:app)
├── setup_milvus.py                 # (đã chuyển sang database/milvus/setup_milvus.py)
├── requirements.txt                # dependencies cho module này
└── README.md
```

Lưu ý về model/ánh xạ cần có trong `output/`:
- `output/q2id.pkl`
- `output/s2id.pkl`
- `output/saint_epoch*.pt` (ví dụ: `saint_epoch3_auc1.0000.pt`)

### 2) Cách chạy API

- Phương pháp 1: Docker Compose (khuyến nghị, xem `docker-compose.yml` ở project root)
```bash
docker-compose up -d
```

- Phương pháp 2: Chạy trực tiếp (local)
  - Cách khuyến nghị (chạy từ project root để import module ổn định):
    ```bash
    pip install -r backend/saint_analysis/requirements.txt
    uvicorn backend.saint_analysis.main:app --host 0.0.0.0 --port 8000 --reload
    ```
  - Nếu bạn đang ở thư mục `backend/saint_analysis` vẫn có thể chạy:
    ```bash
    uvicorn main:app --host 0.0.0.0 --port 8000 --reload
    ```

### 3) Cấu hình môi trường `.env`
Tạo file `.env` tại `backend/saint_analysis`. Ví dụ:
```env
# Đường dẫn dữ liệu và model
DATA_DIR=./data
TRAIN_FILE=saintpp_data/processed/train.tsv
VALID_FILE=saintpp_data/processed/valid.tsv
TEST_FILE=saintpp_data/processed/test.tsv
OUTPUT_DIR=./output
MODEL_PATH=./output/saint_epoch3_auc1.0000.pt
EMBED_DIM=128
DEVICE=cpu

# Milvus (dùng SDK pymilvus)
# KHÔNG dùng dạng có scheme như http://localhost:19530
MILVUS_HOST=localhost
MILVUS_PORT=19530

# Tên collection
PROFILE_COLLECTION=profile_student
SNAPSHOT_COLLECTION=snapshot_student
```

Ghi chú:
- Một số endpoint phụ thuộc Milvus, cần Milvus sẵn sàng và collections đã được tạo.
- `setup_milvus.py` có thể tự động tạo collections và index (xem mục 5).

### 4) Định dạng API: Endpoints, Input/Output

Tất cả responses là JSON. Trừ khi ghi chú khác, mã trạng thái HTTP 200 khi thành công.

- Health Check
  - `GET /`
  - Response:
    ```json
    { "message": "SAINT++ API is running!", "status": "healthy" }
    ```

- Phân tích học sinh
  - `POST /analyze`
  - Request:
    ```json
    { "student_id": "student_001" }
    ```
  - Response (ví dụ):
    ```json
    {
      "student_id": "student_001",
      "low_accuracy_skills": ["math_basic"],
      "slow_response_skills": ["problem_solving"],
      "embedding_vector": [0.12, 0.84, 0.33]
    }
    ```
  - Lỗi 404: `{ "detail": "Không tìm thấy học sinh trong Milvus." }`

- Ghi log tương tác hàng loạt
  - `POST /interaction`
  - Request:
    ```json
    [
      {
        "student_id": "student_001",
        "timestamp": "2024-01-01T10:00:00Z",
        "question_text": "What is 2+2?",
        "answer": "4",
        "skill_id": "math_basic",
        "correct": true,
        "response_time": 2.5
      }
    ]
    ```
  - Response:
    ```json
    { "status": "Success", "profile": { /* hồ sơ cập nhật */ } }
    ```

- Lịch sử tiến bộ
  - `GET /progress/{student_id}`
  - Response (ví dụ):
    ```json
    {
      "student_id": "student_001",
      "progress_history": [
        { "date": "2024-01-01", "score": 75, "skills_improved": ["math_basic"] }
      ]
    }
    ```
  - Lỗi 404: `{ "detail": "Không tìm thấy lịch sử tiến bộ." }`

- Tạo bài tập cá nhân hóa
  - `GET /generate_exercise?student_id={student_id}`
  - Response (ví dụ):
    ```json
    {
      "student_id": "student_001",
      "prompt": "...",
      "suggested_exercises": ["Bài tập 1 ...", "Bài tập 2 ..."]
    }
    ```

- Snapshot tiến bộ
  - `GET /progress_snapshot/{student_id}`
  - Response (ví dụ):
    ```json
    {
      "student_id": "student_001",
      "snapshots": [
        { "timestamp": "2024-01-01T10:00:00Z", "performance": "good" }
      ]
    }
    ```
  - Lỗi 404: `{ "detail": "Không tìm thấy snapshot nào." }`

- Xu hướng kỹ năng
  - `GET /skill_trend?student_id={student_id}&skill_id={skill_id}`
  - Response (ví dụ):
    ```json
    {
      "student_id": "student_001",
      "skill_id": "math_basic",
      "progress": [
        { "timestamp": "2024-01-01", "accuracy": 0.7, "avg_time": 3.2 }
      ]
    }
    ```
  - Lỗi 500 (Milvus): `{ "detail": "Lỗi truy vấn Milvus: ..." }`

### 5) Yêu cầu Database/Collections Milvus

Kết nối mặc định: host `localhost`, port `19530`, database `default`.

- Collection `profile_student`
  - Trường: `student_id` (PK, VARCHAR(100)), `low_accuracy_skills` (VARCHAR(500)), `slow_response_skills` (VARCHAR(500)), `embedding_vector` (FLOAT_VECTOR 128D)

- Collection `snapshot_student`
  - Trường: `id` (PK, INT64), `student_id` (VARCHAR(100)), `timestamp` (VARCHAR(50)), `low_accuracy_skills` (VARCHAR(500)), `slow_response_skills` (VARCHAR(500)), `embedding_vector` (FLOAT_VECTOR 128D)

- Collection `skill_progress_collection`
  - Trường: `id` (PK, INT64), `student_id` (VARCHAR(100)), `skill_id` (VARCHAR(50)), `timestamp` (VARCHAR(50)), `accuracy` (FLOAT), `avg_time` (FLOAT), `progress_vector` (FLOAT_VECTOR 64D)

Tạo tự động bằng script (đã chuẩn hoá tại `database/milvus/setup_milvus.py`):
```bash
python database/milvus/setup_milvus.py
```
Script sẽ:
- Kết nối Milvus theo `MILVUS_HOST`/`MILVUS_PORT`
- Tạo các collections nếu chưa tồn tại
- Tạo index IVF_FLAT cho các vector fields với metric L2

### 6) Test API nhanh

- Chạy toàn bộ hệ thống qua Docker: `docker-compose up -d`
- Test tất cả endpoints:
```bash
python complete_test.py
```

Hoặc dùng cURL:
```bash
curl -X GET "http://localhost:8000/"
curl -X POST "http://localhost:8000/analyze" -H "Content-Type: application/json" -d '{"student_id":"student_001"}'
curl -X POST "http://localhost:8000/interaction" -H "Content-Type: application/json" -d '[{"student_id":"student_001","timestamp":"2024-01-01T10:00:00Z","question_text":"What is 2+2?","answer":"4","skill_id":"math_basic","correct":true,"response_time":2.5}]'
curl -X GET "http://localhost:8000/progress/student_001"
curl -X GET "http://localhost:8000/generate_exercise?student_id=student_001"
```

### 7) Input/Output format tổng hợp

- Kiểu dữ liệu chung:
  - `student_id`: string
  - `timestamp`: ISO string, ví dụ `2025-09-30T02:30:00.000Z`
  - `skill_id`: string
  - `correct`: boolean
  - `response_time`: float (giây)

- Hồ sơ học sinh (ví dụ) trả về bởi `/analyze` hoặc sau `/interaction`:
```json
{
  "student_id": "HS001",
  "low_accuracy_skills": ["S10","S11"],
  "slow_response_skills": ["S05"],
  "embedding_vector": [0.12, 0.84, 0.33]
}
```

### 8) Monitoring & UI

- Milvus UI (Attu): `http://localhost:3000` (kết nối `localhost:19530/default`)
- MinIO Console: `http://localhost:9001` (user/pass: `minioadmin`)

### 9) Troubleshooting

- Kết nối Milvus: đảm bảo etcd → MinIO → Milvus khởi động theo thứ tự, port 19530 mở.
- Chạy `python database/milvus/setup_milvus.py` nếu collections thiếu hoặc lỗi index/vector dims.
- Kiểm tra đủ files trong `output/` (q2id.pkl, s2id.pkl, trọng số mô hình).
- Xem logs Docker: `docker-compose logs saint_api`, `docker-compose logs milvus-standalone`.
- Lỗi ConnectionConfigException của pymilvus: đặt biến môi trường dạng không có scheme:
  - `MILVUS_HOST=localhost`
  - `MILVUS_PORT=19530`
  - Tránh đặt `MILVUS_URL=http://localhost:19530`. Nếu dùng `MILVUS_URL`, dùng dạng `localhost:19530`.

### 10) Ghi chú triển khai

- Dev (từ project root): `uvicorn backend.saint_analysis.main:app --reload`
- Prod: `uvicorn backend.saint_analysis.main:app --host 0.0.0.0 --port 8000 --workers 4`

Ghi chú hiệu năng:
- Ứng dụng kết nối Milvus một lần ở giai đoạn startup, giảm lỗi “Not connected/URI”.
- Các collection được load khi cần; tránh gọi `load()` lặp lại cho mỗi request.


