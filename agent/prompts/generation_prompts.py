"""
Question Generation Prompts
==========================

Prompts for generating educational questions using LLM.
"""

class GenerationPrompts:
    """Collection of prompts for question generation"""
    
    # Main generation system prompt
    GENERATION_SYSTEM = """Bạn là một chuyên gia giáo dục tiểu học, chuyên về việc tạo câu hỏi học tập phù hợp với từng độ tuổi.
                         Nhiệm vụ của bạn là tạo ra những câu hỏi chất lượng cao, phù hợp với trình độ học sinh và tuân thủ chương trình giáo dục chính thức.
                         
                         Nguyên tắc tạo câu hỏi:
                         - Sử dụng ngôn ngữ đơn giản, dễ hiểu cho học sinh tiểu học
                         - Đảm bảo tính chính xác về mặt kiến thức
                         - Phù hợp với trình độ phát triển của học sinh
                         - Khuyến khích tư duy và học tập tích cực
                         - Tuân thủ phương pháp giáo dục hiện đại"""
    
    @staticmethod
    def multiple_choice_generation(topic: str, grade: int, subject: str, 
                                 teacher_context: list, textbook_context: list) -> str:
        return f"""Tạo câu hỏi trắc nghiệm cho học sinh lớp {grade} về chủ đề: {topic}
                
                Môn học: {subject}
                
                Hướng dẫn từ giáo viên:
                {chr(10).join([f"- {ctx}" for ctx in teacher_context[:3]])}
                
                Ví dụ từ sách giáo khoa:
                {chr(10).join([f"- {ctx}" for ctx in textbook_context[:3]])}
                
                Yêu cầu:
                1. Tạo câu hỏi phù hợp với trình độ lớp {grade}
                2. Sử dụng ngôn ngữ đơn giản, dễ hiểu
                3. Tạo đúng 4 đáp án (A, B, C, D)
                4. Chỉ có 1 đáp án đúng
                5. Các đáp án sai phải hợp lý và có tính gây nhiễu
                6. Thêm giải thích ngắn gọn cho đáp án đúng
                
                Định dạng JSON:
                {{
                    "question": "Câu hỏi...",
                    "answers": [
                        {{"text": "Đáp án A", "correct": true}},
                        {{"text": "Đáp án B", "correct": false}},
                        {{"text": "Đáp án C", "correct": false}},
                        {{"text": "Đáp án D", "correct": false}}
                    ],
                    "explanation": "Giải thích ngắn gọn cho đáp án đúng"
                }}"""
    
    @staticmethod
    def true_false_generation(topic: str, grade: int, subject: str,
                            teacher_context: list, textbook_context: list) -> str:
        return f"""Tạo câu hỏi Đúng/Sai cho học sinh lớp {grade} về chủ đề: {topic}
                
                Môn học: {subject}
                
                Hướng dẫn từ giáo viên:
                {chr(10).join([f"- {ctx}" for ctx in teacher_context[:3]])}
                
                Ví dụ từ sách giáo khoa:
                {chr(10).join([f"- {ctx}" for ctx in textbook_context[:3]])}
                
                Yêu cầu:
                1. Tạo câu khẳng định rõ ràng, không mơ hồ
                2. Phù hợp với trình độ lớp {grade}
                3. Câu khẳng định có thể là đúng hoặc sai
                4. Sử dụng ngôn ngữ đơn giản
                5. Thêm giải thích tại sao đúng hoặc sai
                
                Định dạng JSON:
                {{
                    "question": "Câu khẳng định...",
                    "answers": [
                        {{"text": "Đúng", "correct": true}},
                        {{"text": "Sai", "correct": false}}
                    ],
                    "explanation": "Giải thích tại sao đúng hoặc sai"
                }}"""
    
    @staticmethod
    def fill_in_blank_generation(topic: str, grade: int, subject: str,
                               teacher_context: list, textbook_context: list) -> str:
        return f"""Tạo câu hỏi điền vào chỗ trống cho học sinh lớp {grade} về chủ đề: {topic}
                
                Môn học: {subject}
                
                Hướng dẫn từ giáo viên:
                {chr(10).join([f"- {ctx}" for ctx in teacher_context[:3]])}
                
                Ví dụ từ sách giáo khoa:
                {chr(10).join([f"- {ctx}" for ctx in textbook_context[:3]])}
                
                Yêu cầu:
                1. Tạo câu có chỗ trống cần điền
                2. Phù hợp với trình độ lớp {grade}
                3. Sử dụng ngôn ngữ đơn giản
                4. Tạo 4 đáp án gợi ý (1 đúng, 3 sai)
                5. Các đáp án sai phải hợp lý
                6. Thêm giải thích cho đáp án đúng
                
                Định dạng JSON:
                {{
                    "question": "Câu hỏi có chỗ trống ___ cần điền",
                    "answers": [
                        {{"text": "Đáp án đúng", "correct": true}},
                        {{"text": "Đáp án sai 1", "correct": false}},
                        {{"text": "Đáp án sai 2", "correct": false}},
                        {{"text": "Đáp án sai 3", "correct": false}}
                    ],
                    "explanation": "Giải thích tại sao đáp án này đúng"
                }}"""
    
    @staticmethod
    def math_specific_generation(topic: str, grade: int, skill: str,
                               teacher_context: list, textbook_context: list) -> str:
        return f"""Tạo câu hỏi toán học cho học sinh lớp {grade} về: {topic}
                
                Kỹ năng: {skill}
                
                Hướng dẫn từ giáo viên:
                {chr(10).join([f"- {ctx}" for ctx in teacher_context[:3]])}
                
                Ví dụ từ sách giáo khoa:
                {chr(10).join([f"- {ctx}" for ctx in textbook_context[:3]])}
                
                Yêu cầu đặc biệt cho toán học:
                1. Sử dụng số liệu phù hợp với lớp {grade}
                2. Đảm bảo tính toán chính xác
                3. Sử dụng từ ngữ toán học đơn giản
                4. Tạo câu hỏi thực tế, gần gũi với học sinh
                5. Các đáp án sai phải là lỗi thường gặp của học sinh
                6. Giải thích rõ ràng cách giải
                
                Định dạng JSON:
                {{
                    "question": "Câu hỏi toán học...",
                    "answers": [
                        {{"text": "Kết quả đúng", "correct": true}},
                        {{"text": "Lỗi thường gặp 1", "correct": false}},
                        {{"text": "Lỗi thường gặp 2", "correct": false}},
                        {{"text": "Lỗi thường gặp 3", "correct": false}}
                    ],
                    "explanation": "Hướng dẫn giải chi tiết"
                }}"""
    
    @staticmethod
    def language_specific_generation(topic: str, grade: int, skill: str,
                                   teacher_context: list, textbook_context: list) -> str:
        return f"""Tạo câu hỏi tiếng Việt cho học sinh lớp {grade} về: {topic}
                
                Kỹ năng: {skill}
                
                Hướng dẫn từ giáo viên:
                {chr(10).join([f"- {ctx}" for ctx in teacher_context[:3]])}
                
                Ví dụ từ sách giáo khoa:
                {chr(10).join([f"- {ctx}" for ctx in textbook_context[:3]])}
                
                Yêu cầu đặc biệt cho tiếng Việt:
                1. Sử dụng từ vựng phù hợp với lớp {grade}
                2. Đảm bảo ngữ pháp chính xác
                3. Tạo câu hỏi về từ vựng, ngữ pháp, hoặc hiểu biết
                4. Sử dụng ví dụ gần gũi với học sinh
                5. Các đáp án sai phải hợp lý về mặt ngôn ngữ
                6. Giải thích rõ ràng về ngữ pháp hoặc từ vựng
                
                Định dạng JSON:
                {{
                    "question": "Câu hỏi tiếng Việt...",
                    "answers": [
                        {{"text": "Đáp án đúng", "correct": true}},
                        {{"text": "Đáp án sai 1", "correct": false}},
                        {{"text": "Đáp án sai 2", "correct": false}},
                        {{"text": "Đáp án sai 3", "correct": false}}
                    ],
                    "explanation": "Giải thích về ngữ pháp/từ vựng"
                }}"""
    
    @staticmethod
    def difficulty_adjustment(question: str, current_grade: int, target_grade: int) -> str:
        return f"""Điều chỉnh độ khó câu hỏi từ lớp {current_grade} xuống lớp {target_grade}
                
                Câu hỏi hiện tại:
                {question}
                
                Yêu cầu điều chỉnh:
                1. Giảm độ phức tạp của từ vựng
                2. Đơn giản hóa cấu trúc câu
                3. Sử dụng số liệu nhỏ hơn (nếu là toán)
                4. Tăng tính trực quan, cụ thể
                5. Giảm số bước suy luận cần thiết
                6. Đảm bảo vẫn giữ được ý nghĩa giáo dục
                
                Trả về câu hỏi đã được điều chỉnh phù hợp với lớp {target_grade}."""
    
    @staticmethod
    def explanation_enhancement(question: str, answer: str, grade: int) -> str:
        return f"""Tạo giải thích chi tiết cho câu hỏi lớp {grade}
                
                Câu hỏi: {question}
                Đáp án đúng: {answer}
                
                Yêu cầu giải thích:
                1. Giải thích tại sao đáp án này đúng
                2. Sử dụng ngôn ngữ phù hợp với lớp {grade}
                3. Đưa ra ví dụ minh họa nếu cần
                4. Giải thích tại sao các đáp án khác sai
                5. Đưa ra mẹo nhớ hoặc cách học hiệu quả
                6. Tối đa 2-3 câu, ngắn gọn nhưng đầy đủ
                
                Trả về giải thích rõ ràng và hữu ích cho học sinh."""

