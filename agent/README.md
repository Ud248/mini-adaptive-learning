# 🧠 ALQ-Agent (Adaptive Learning Question Agent)

Hệ thống tạo câu hỏi học tập thích ứng cho học sinh tiểu học, sử dụng AI để tạo ra các câu hỏi cá nhân hóa dựa trên điểm yếu và lịch sử học tập của từng học sinh.

## 📋 Tổng quan

ALQ-Agent là một module AI chuyên biệt trong hệ thống Mini adaptive learning, có nhiệm vụ:
- **Tạo câu hỏi cá nhân hóa** dựa trên điểm yếu của học sinh
- **Sử dụng nội dung chính thức** từ sách giáo viên và sách giáo khoa
- **Đảm bảo chất lượng** thông qua quy trình validation đa bước
- **Tích hợp với vector databases** để truy xuất context phù hợp

## 🏗️ Kiến trúc

```
agent/
├── tools/                    # Các công cụ chuyên biệt
│   ├── rag_tool.py          # Truy xuất context từ vector DB
│   ├── template_tool.py     # Cung cấp mẫu câu hỏi
│   ├── question_generation_tool.py  # Tạo câu hỏi
│   └── validation_tool.py   # Kiểm tra chất lượng
├── models/                   # Các model AI
│   └── embedding_model.py   # Wrapper cho embedding service
├── prompts/                  # Prompts cho LLM interactions
│   ├── rag_prompts.py       # Prompts cho RAG operations
│   ├── generation_prompts.py # Prompts cho question generation
│   ├── validation_prompts.py # Prompts cho validation
│   ├── template_prompts.py  # Prompts cho template selection
│   └── demo_prompts.py      # Demo prompts usage
├── workflow/                 # Quy trình chính
│   └── agent_workflow.py    # Workflow orchestration
├── demo.py                  # Demo và test
└── README.md               # Tài liệu này
```

## 🚀 Cài đặt và sử dụng

### 1. Cài đặt dependencies

```bash
# Đảm bảo các dependencies cần thiết đã được cài đặt
pip install sentence-transformers torch
pip install pymilvus
pip install fastapi
```

### 2. Sử dụng cơ bản

```python
from agent import create_alq_agent

# Tạo ALQ agent
agent = create_alq_agent(verbose=True)

# Profile học sinh
student_profile = {
    'grade': 1,
    'subject': 'Toán',
    'skill': 'S5',
    'skill_name': 'Mấy và mấy',
    'low_accuracy_skills': ['S5'],
    'slow_response_skills': [],
    'difficulty': 'easy'
}

# Tạo câu hỏi
result = agent.run(student_profile, topic="phép cộng cơ bản")

# Kiểm tra kết quả
if result.question:
    print(f"Câu hỏi: {result.question.question}")
    for i, answer in enumerate(result.question.answers, 1):
        status = "✓" if answer.get('correct', False) else " "
        print(f"{i}. {status} {answer.get('text', 'N/A')}")
```

### 3. Sử dụng nâng cao

```python
# Tạo câu hỏi cho nhiều học sinh
student_profiles = [
    {
        'grade': 1,
        'subject': 'Toán',
        'skill': 'S5',
        'skill_name': 'Mấy và mấy',
        'low_accuracy_skills': ['S5'],
        'slow_response_skills': [],
        'difficulty': 'easy'
    },
    {
        'grade': 2,
        'subject': 'Toán',
        'skill': 'S6',
        'skill_name': 'Phép trừ',
        'low_accuracy_skills': ['S6'],
        'slow_response_skills': [],
        'difficulty': 'medium'
    }
]

# Chạy batch processing
results = agent.run_batch(student_profiles)

# Xem thống kê
stats = agent.get_workflow_stats(results)
print(f"Tỷ lệ thành công: {stats['success_rate']:.2%}")
```

## 🧩 Các thành phần chính

### 1. RAGTool
- Truy xuất context từ `sgv_collection` (sách giáo viên)
- Truy xuất context từ `baitap_collection` (sách giáo khoa)
- Sử dụng embedding model tiếng Việt

### 2. TemplateTool
- Cung cấp mẫu câu hỏi cho các môn học khác nhau
- Hỗ trợ: Multiple choice, True/False, Fill in the blank
- Tự động chọn mẫu phù hợp với grade và subject

### 3. QuestionGenerationTool
- Tạo câu hỏi dựa trên context và template
- Tích hợp với LLM (OpenAI, Claude, hoặc SAINT)
- Đảm bảo ngôn ngữ phù hợp với độ tuổi

### 4. ValidationTool
- Kiểm tra độ chính xác toán học/thực tế
- Đánh giá độ khó phù hợp với grade
- Kiểm tra tính rõ ràng và phù hợp giáo dục

### 5. Prompts Module
- **RAGPrompts**: Prompts cho context retrieval và query processing
- **GenerationPrompts**: Prompts cho question generation với các loại khác nhau
- **ValidationPrompts**: Prompts cho validation đa tiêu chí
- **TemplatePrompts**: Prompts cho template selection và customization

## 🔧 Cấu hình

### Embedding Model
```python
# Sử dụng model tiếng Việt có sẵn
from agent.models.embedding_model import create_alq_embedder

embedder = create_alq_embedder(
    model_name='dangvantuan/vietnamese-document-embedding',
    batch_size=16,
    verbose=True
)
```

### Vector Database
```python
# Cấu hình Milvus collections
collections = {
    'teacher': 'sgv_collection',    # Sách giáo viên
    'textbook': 'baitap_collection' # Sách giáo khoa
}
```

## 📊 Workflow

1. **Context Understanding**: Phân tích profile học sinh
2. **Dual Knowledge Retrieval**: Truy xuất từ teacher_book và textbook
3. **Template Selection**: Chọn mẫu câu hỏi phù hợp
4. **Question Generation**: Tạo câu hỏi bằng LLM
5. **Validation**: Kiểm tra chất lượng đa tiêu chí
6. **Return Result**: Trả về câu hỏi đã được validate

## 🧪 Testing

```bash
# Chạy demo
python agent/demo.py

# Test prompts module
python agent/prompts/demo_prompts.py

# Test từng component
python agent/tools/rag_tool.py
python agent/tools/template_tool.py
python agent/tools/question_generation_tool.py
python agent/tools/validation_tool.py
python agent/workflow/agent_workflow.py
```

## 📝 Prompts Usage

### Sử dụng prompts module

```python
from agent.prompts import GenerationPrompts, ValidationPrompts

# Tạo prompt cho question generation
prompt = GenerationPrompts.multiple_choice_generation(
    topic="phép cộng cơ bản",
    grade=1,
    subject="Toán",
    teacher_context=["Hướng dẫn dạy phép cộng"],
    textbook_context=["2 + 3 = 5"]
)

# Tạo prompt cho validation
validation_prompt = ValidationPrompts.accuracy_validation(
    question="2 + 3 = ?",
    answers=[{"text": "5", "correct": True}],
    subject="Toán",
    grade=1
)
```

### Custom prompts

```python
# Tạo custom prompt cho specific use case
custom_prompt = GenerationPrompts.math_specific_generation(
    topic="phép nhân",
    grade=2,
    skill="S7",
    teacher_context=["Hướng dẫn dạy phép nhân"],
    textbook_context=["3 × 4 = 12"]
)
```

## 📈 Performance

- **Response Time**: < 5 giây cho mỗi câu hỏi
- **Accuracy Rate**: > 95% validation pass rate
- **Scalability**: Hỗ trợ concurrent requests
- **Memory Efficient**: Tối ưu GPU memory cho embedding

## 🔗 Tích hợp

### Với Backend API
```python
# Trong FastAPI endpoint
@app.post("/agent/generate")
async def generate_question(student_profile: dict):
    agent = create_alq_agent()
    result = agent.run(student_profile)
    return result.question
```

### Với Frontend
```javascript
// Gọi API từ frontend
const response = await fetch('/agent/generate', {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify(studentProfile)
});
const question = await response.json();
```

## 🛠️ Troubleshooting

### Lỗi thường gặp

1. **Import Error**: Đảm bảo đã cài đặt đầy đủ dependencies
2. **Milvus Connection**: Kiểm tra kết nối đến vector database
3. **Embedding Model**: Đảm bảo model đã được download
4. **Memory Issues**: Giảm batch_size nếu gặp lỗi OOM

### Debug Mode
```python
# Bật verbose mode để debug
agent = create_alq_agent(verbose=True)
```

## 📝 Changelog

### v1.0.0
- ✅ Hoàn thành core functionality
- ✅ Tích hợp với existing embedding service
- ✅ Hỗ trợ multiple question types
- ✅ Validation system đa tiêu chí
- ✅ Batch processing support

## 🤝 Contributing

1. Fork repository
2. Tạo feature branch
3. Commit changes
4. Push to branch
5. Tạo Pull Request

## 📄 License

MIT License - xem file LICENSE để biết thêm chi tiết.

## 📞 Support

Nếu gặp vấn đề, vui lòng tạo issue trên GitHub hoặc liên hệ team phát triển.
