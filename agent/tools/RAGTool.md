# RAGTool

RAGTool truy xuất ngữ cảnh dạy học (SGV) và bài tập SGK từ Milvus theo chiến lược 2 bước: lọc metadata rồi fallback tìm kiếm vector, sau đó rerank và khử trùng lặp. Kết quả dùng cho sinh câu hỏi cá nhân hóa trong ALQ-Agent.

## Phụ thuộc
- Milvus client nội bộ: `database/milvus/milvus_client.py`
- Embedder nội bộ: `database/embeddings/local_embedder.py`
- Cấu hình: `configs/agent.yaml` (khóa `rag`)

## Cấu hình
Ví dụ `configs/agent.yaml`:
```yaml
rag:
  topk_sgv: 5
  topk_sgk: 20
  cache_ttl_s: 900
```
Các giá trị có thể override qua tham số `config` khi khởi tạo `RAGTool`.

## API
```python
from agent.tools.rag_tool import RAGTool

rag = RAGTool()
result = rag.query(
    grade=1,
    skill="S5",
    skill_name="Mấy và mấy",
    topk_sgv=5,
    topk_sgk=20,
)

teacher_chunks = result["teacher_context"]
textbook_chunks = result["textbook_context"]
```
Mỗi phần tử có dạng:
```json
{
  "id": "...",
  "text": "...",
  "source": "...",
  "lesson": "...",
  "score": 0.0
}
```
Ghi chú: SGV dùng `content` làm `text`; SGK dùng chuỗi `"Q: {question}\nA: {answer}"`.

## Chiến lược truy vấn
1. Lọc metadata nếu có `skill_name`: `normalized_lesson == normalize(skill_name)` → gọi `query()` Milvus.
2. Nếu rỗng, fallback vector search:
   - Tạo văn bản truy vấn: `"{skill_name or skill} lớp {grade}"`
   - Embed → gọi `search()` Milvus với `metric_type=COSINE`.
3. Rerank: `final = 0.6*sim + 0.3*lesson_match + 0.1*grade_match` (sim lấy từ distance → similarity).
4. Khử trùng lặp bằng MD5 theo `text`, giữ bản điểm cao nhất.

## Cache
- Cache trong bộ nhớ theo key `(grade, skill, skill_name, topk_sgv, topk_sgk)`.
- TTL lấy từ `rag.cache_ttl_s` (mặc định 900 giây).

## Kiểm thử
Chạy unit tests:
```bash
pytest -q tests/test_rag_tool.py
```
Bao phủ:
- Ưu tiên kết quả filter; fallback vector khi rỗng
- Rerank + khử trùng lặp
- Cache TTL

## Ghi chú
Nếu Milvus/Embedder không khả dụng, tool tự degrade: trả mảng rỗng hoặc bỏ qua fallback (không raise lỗi ra pipeline).
