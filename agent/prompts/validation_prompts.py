SYSTEM_PROMPT = (
    "Bạn là bộ kiểm định chất lượng câu hỏi cho học sinh lớp 1. "
    "Nhiệm vụ: đánh giá độ rõ ràng, đúng/sai, phù hợp lứa tuổi, bám ngữ cảnh. "
    "Chỉ trả về JSON, không kèm giải thích ngoài JSON."
)

CRITIQUE_USER_TEMPLATE = (
    "Hãy kiểm định danh sách câu hỏi sau. Nếu phát hiện vấn đề, hãy ghi thành các issue và đề xuất sửa.\n\n"
    "YÊU CẦU:\n"
    "- Chỉ cho phép 3 loại: multiple_choice, true_false, fill_blank\n"
    "- Số đáp án: multiple_choice/fill_blank = 4; true_false = 2; đúng 1 đáp án\n"
    "- Ngôn ngữ rõ ràng, phù hợp lớp 1\n"
    "- Bám teacher_context/textbook_context nếu có\n\n"
    "INPUT:\n"
    "questions: {questions}\n\n"
    "teacher_context: {teacher_context}\n\n"
    "textbook_context: {textbook_context}\n\n"
    "OUTPUT JSON:\n"
    "{\n"
    "  \"issues\": [{\n"
    "    \"question_id\": \"...\",\n"
    "    \"code\": \"LLM_CRITIQUE\",\n"
    "    \"message\": \"...\"\n"
    "  }],\n"
    "  \"suggested_fixes\": [{\n"
    "    \"question_id\": \"...\",\n"
    "    \"patch\": {\"question_text\": \"...\", \"answers\": [...]},\n"
    "    \"reason\": \"...\"\n"
    "  }]\n"
    "}"
)

