"""
Validation Prompts
=================

Prompts for validating generated questions for accuracy, difficulty, and educational alignment.
"""

class ValidationPrompts:
    """Collection of prompts for question validation"""
    
    # Main validation system prompt
    VALIDATION_SYSTEM = """Bạn là một chuyên gia đánh giá giáo dục, chuyên về việc kiểm tra và đánh giá chất lượng câu hỏi học tập.
                         Nhiệm vụ của bạn là đánh giá câu hỏi theo các tiêu chí: độ chính xác, độ khó, tính rõ ràng, và sự phù hợp với chương trình giáo dục.
                         
                         Nguyên tắc đánh giá:
                         - Độ chính xác: Kiến thức phải chính xác, không có lỗi
                         - Độ khó: Phù hợp với trình độ phát triển của học sinh
                         - Tính rõ ràng: Câu hỏi dễ hiểu, không gây nhầm lẫn
                         - Phù hợp giáo dục: Tuân thủ phương pháp và mục tiêu giáo dục"""
    
    @staticmethod
    def accuracy_validation(question: str, answers: list, subject: str, grade: int) -> str:
        return f"""Đánh giá độ chính xác của câu hỏi {subject} lớp {grade}
                
                Câu hỏi: {question}
                
                Các đáp án:
                {chr(10).join([f"- {ans.get('text', 'N/A')} ({'Đúng' if ans.get('correct', False) else 'Sai'})" for ans in answers])}
                
                Yêu cầu đánh giá:
                1. Kiểm tra tính chính xác về mặt kiến thức
                2. Xác minh đáp án đúng có thực sự đúng không
                3. Kiểm tra các đáp án sai có hợp lý không
                4. Đánh giá mức độ phù hợp với chương trình lớp {grade}
                5. Kiểm tra có lỗi logic hoặc ngữ pháp không
                
                Trả về đánh giá theo thang điểm 0-1:
                {{
                    "accuracy_score": 0.95,
                    "is_correct": true,
                    "feedback": "Câu hỏi chính xác về mặt kiến thức",
                    "issues": ["Không có vấn đề nào"],
                    "suggestions": ["Có thể thêm ví dụ minh họa"]
                }}"""
    
    @staticmethod
    def difficulty_validation(question: str, grade: int, subject: str) -> str:
        return f"""Đánh giá độ khó của câu hỏi {subject} lớp {grade}
                
                Câu hỏi: {question}
                
                Yêu cầu đánh giá:
                1. Từ vựng có phù hợp với lớp {grade} không
                2. Khái niệm có quá phức tạp không
                3. Số bước suy luận có phù hợp không
                4. Có cần kiến thức nền tảng gì không
                5. Thời gian suy nghĩ có hợp lý không
                
                Tiêu chí đánh giá:
                - Lớp 1-2: Từ vựng đơn giản, khái niệm cơ bản
                - Lớp 3-4: Có thể có từ vựng phức tạp hơn
                - Lớp 5: Có thể yêu cầu tư duy logic
                
                Trả về đánh giá:
                {{
                    "difficulty_score": 0.8,
                    "is_appropriate": true,
                    "feedback": "Độ khó phù hợp với lớp {grade}",
                    "complexity_issues": [],
                    "adjustment_suggestions": []
                }}"""
    
    @staticmethod
    def clarity_validation(question: str, answers: list, grade: int) -> str:
        return f"""Đánh giá tính rõ ràng của câu hỏi lớp {grade}
                
                Câu hỏi: {question}
                
                Các đáp án:
                {chr(10).join([f"- {ans.get('text', 'N/A')}" for ans in answers])}
                
                Yêu cầu đánh giá:
                1. Câu hỏi có rõ ràng, dễ hiểu không
                2. Có từ ngữ gây nhầm lẫn không
                3. Các đáp án có rõ ràng không
                4. Có câu hỏi phụ hoặc yêu cầu không rõ không
                5. Ngôn ngữ có phù hợp với độ tuổi không
                
                Tiêu chí:
                - Câu hỏi ngắn gọn, súc tích
                - Từ ngữ đơn giản, dễ hiểu
                - Không có từ lóng hoặc thuật ngữ phức tạp
                - Các đáp án rõ ràng, không mơ hồ
                
                Trả về đánh giá:
                {{
                    "clarity_score": 0.9,
                    "is_clear": true,
                    "feedback": "Câu hỏi rõ ràng, dễ hiểu",
                    "unclear_elements": [],
                    "improvement_suggestions": []
                }}"""
    
    @staticmethod
    def pedagogical_validation(question: str, teacher_context: list, grade: int, subject: str) -> str:
        return f"""Đánh giá sự phù hợp với phương pháp giáo dục
                
                Câu hỏi: {question}
                Lớp: {grade}
                Môn: {subject}
                
                Hướng dẫn từ giáo viên:
                {chr(10).join([f"- {ctx}" for ctx in teacher_context[:3]])}
                
                Yêu cầu đánh giá:
                1. Câu hỏi có tuân thủ phương pháp giảng dạy không
                2. Có khuyến khích tư duy tích cực không
                3. Có phù hợp với mục tiêu học tập không
                4. Có tạo cơ hội học tập có ý nghĩa không
                5. Có phù hợp với phong cách học tập của học sinh không
                
                Tiêu chí:
                - Khuyến khích tư duy, không chỉ ghi nhớ
                - Tạo cơ hội thực hành và ứng dụng
                - Phù hợp với phương pháp giáo dục hiện đại
                - Khuyến khích học tập tích cực
                
                Trả về đánh giá:
                {{
                    "pedagogical_score": 0.85,
                    "is_appropriate": true,
                    "feedback": "Phù hợp với phương pháp giáo dục",
                    "pedagogical_issues": [],
                    "improvement_suggestions": []
                }}"""
    
    @staticmethod
    def language_appropriateness_validation(question: str, answers: list, grade: int) -> str:
        return f"""Đánh giá sự phù hợp ngôn ngữ cho lớp {grade}
                
                Câu hỏi: {question}
                
                Các đáp án:
                {chr(10).join([f"- {ans.get('text', 'N/A')}" for ans in answers])}
                
                Yêu cầu đánh giá:
                1. Từ vựng có phù hợp với độ tuổi không
                2. Cấu trúc câu có phù hợp không
                3. Có sử dụng tiếng Việt chuẩn không
                4. Có từ ngữ khó hiểu không
                5. Có phù hợp với văn hóa Việt Nam không
                
                Tiêu chí theo độ tuổi:
                - Lớp 1-2: Từ vựng cơ bản, câu ngắn
                - Lớp 3-4: Có thể có từ vựng phức tạp hơn
                - Lớp 5: Có thể sử dụng câu dài hơn
                
                Trả về đánh giá:
                {{
                    "language_score": 0.9,
                    "is_appropriate": true,
                    "feedback": "Ngôn ngữ phù hợp với độ tuổi",
                    "language_issues": [],
                    "adjustment_suggestions": []
                }}"""
    
    @staticmethod
    def comprehensive_validation(question: str, answers: list, grade: int, subject: str,
                               teacher_context: list, textbook_context: list) -> str:
        return f"""Đánh giá toàn diện câu hỏi {subject} lớp {grade}
                
                Câu hỏi: {question}
                
                Các đáp án:
                {chr(10).join([f"- {ans.get('text', 'N/A')} ({'Đúng' if ans.get('correct', False) else 'Sai'})" for ans in answers])}
                
                Hướng dẫn từ giáo viên:
                {chr(10).join([f"- {ctx}" for ctx in teacher_context[:2]])}
                
                Ví dụ từ sách giáo khoa:
                {chr(10).join([f"- {ctx}" for ctx in textbook_context[:2]])}
                
                Yêu cầu đánh giá toàn diện:
                1. Độ chính xác (Accuracy): Kiến thức có đúng không
                2. Độ khó (Difficulty): Có phù hợp với lớp {grade} không
                3. Tính rõ ràng (Clarity): Có dễ hiểu không
                4. Phù hợp giáo dục (Pedagogical): Có tuân thủ phương pháp không
                5. Phù hợp ngôn ngữ (Language): Có phù hợp với độ tuổi không
                
                Trả về đánh giá tổng hợp:
                {{
                    "overall_score": 0.88,
                    "validation_status": "approved",
                    "criteria_scores": {{
                        "accuracy": 0.95,
                        "difficulty": 0.85,
                        "clarity": 0.90,
                        "pedagogical": 0.85,
                        "language": 0.90
                    }},
                    "is_valid": true,
                    "feedback": "Câu hỏi đạt yêu cầu chất lượng",
                    "suggestions": ["Có thể thêm ví dụ minh họa"],
                    "issues": []
                }}"""
    
    @staticmethod
    def batch_validation_summary(validation_results: list) -> str:
        return f"""Tóm tắt đánh giá hàng loạt câu hỏi
                
                Kết quả đánh giá:
                {chr(10).join([f"- Câu hỏi {i+1}: {result.get('validation_status', 'unknown')} (Score: {result.get('overall_score', 0):.2f})" for i, result in enumerate(validation_results)])}
                
                Yêu cầu tóm tắt:
                1. Tỷ lệ câu hỏi đạt yêu cầu
                2. Các vấn đề thường gặp
                3. Điểm mạnh của bộ câu hỏi
                4. Gợi ý cải thiện tổng thể
                5. Đánh giá chất lượng chung
                
                Trả về tóm tắt:
                {{
                    "total_questions": {len(validation_results)},
                    "approved_count": 0,
                    "needs_revision_count": 0,
                    "rejected_count": 0,
                    "approval_rate": 0.0,
                    "average_score": 0.0,
                    "common_issues": [],
                    "strengths": [],
                    "overall_assessment": "Đánh giá tổng thể",
                    "recommendations": []
                }}"""

