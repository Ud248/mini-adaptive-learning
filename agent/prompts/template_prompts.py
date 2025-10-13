"""
Template Selection Prompts
=========================

Prompts for selecting and customizing question templates.
"""

class TemplatePrompts:
    """Collection of prompts for template selection and customization"""
    
    # Template selection system prompt
    TEMPLATE_SELECTION_SYSTEM = """Bạn là chuyên gia thiết kế câu hỏi giáo dục, chuyên về việc lựa chọn và tùy chỉnh mẫu câu hỏi phù hợp.
                                  Nhiệm vụ của bạn là phân tích yêu cầu và chọn mẫu câu hỏi tối ưu cho từng tình huống học tập cụ thể.
                                  
                                  Nguyên tắc lựa chọn:
                                  - Phù hợp với môn học và chủ đề
                                  - Phù hợp với trình độ học sinh
                                  - Khuyến khích tư duy và học tập tích cực
                                  - Dễ hiểu và dễ thực hiện"""
    
    @staticmethod
    def template_selection(subject: str, grade: int, topic: str, difficulty: str) -> str:
        return f"""Lựa chọn mẫu câu hỏi phù hợp
                
                Môn học: {subject}
                Lớp: {grade}
                Chủ đề: {topic}
                Độ khó: {difficulty}
                
                Yêu cầu lựa chọn:
                1. Phân tích chủ đề và xác định loại câu hỏi phù hợp
                2. Xem xét trình độ lớp {grade}
                3. Đánh giá độ khó {difficulty}
                4. Chọn mẫu câu hỏi tối ưu
                
                Các loại mẫu có sẵn:
                - Multiple Choice: Phù hợp cho kiểm tra kiến thức cơ bản
                - True/False: Phù hợp cho khái niệm đơn giản
                - Fill in the Blank: Phù hợp cho từ vựng, công thức
                - Matching: Phù hợp cho mối quan hệ, phân loại
                - Sequence: Phù hợp cho quy trình, thứ tự
                
                Trả về lựa chọn:
                {{
                    "selected_template": "multiple_choice",
                    "reasoning": "Lý do chọn mẫu này",
                    "customization_needed": false,
                    "template_parameters": {{
                        "options_count": 4,
                        "difficulty_level": "{difficulty}",
                        "grade_appropriate": true
                    }}
                }}"""
    
    @staticmethod
    def template_customization(template: str, subject: str, grade: int, specific_requirements: str) -> str:
        return f"""Tùy chỉnh mẫu câu hỏi
                
                Mẫu gốc: {template}
                Môn học: {subject}
                Lớp: {grade}
                Yêu cầu đặc biệt: {specific_requirements}
                
                Yêu cầu tùy chỉnh:
                1. Phân tích mẫu gốc
                2. Xác định các yếu tố cần điều chỉnh
                3. Tùy chỉnh cho phù hợp với yêu cầu
                4. Đảm bảo vẫn giữ được cấu trúc cơ bản
                
                Các yếu tố có thể tùy chỉnh:
                - Số lượng đáp án
                - Độ khó của câu hỏi
                - Cấu trúc câu hỏi
                - Loại đáp án
                - Định dạng hiển thị
                
                Trả về mẫu đã tùy chỉnh:
                {{
                    "customized_template": {{
                        "type": "multiple_choice",
                        "pattern": "Mẫu câu hỏi đã tùy chỉnh",
                        "options_count": 4,
                        "customizations": ["Danh sách các tùy chỉnh đã thực hiện"]
                    }},
                    "changes_made": ["Mô tả các thay đổi"],
                    "compatibility_check": true
                }}"""
    
    @staticmethod
    def template_validation(template: str, subject: str, grade: int) -> str:
        return f"""Kiểm tra tính hợp lệ của mẫu câu hỏi
                
                Mẫu: {template}
                Môn học: {subject}
                Lớp: {grade}
                
                Yêu cầu kiểm tra:
                1. Cấu trúc mẫu có đúng không
                2. Có phù hợp với môn học không
                3. Có phù hợp với lớp {grade} không
                4. Có thể tạo câu hỏi từ mẫu này không
                5. Có cần điều chỉnh gì không
                
                Tiêu chí đánh giá:
                - Cấu trúc rõ ràng, logic
                - Phù hợp với môn học
                - Phù hợp với trình độ
                - Dễ sử dụng và tùy chỉnh
                - Có thể tạo ra câu hỏi chất lượng
                
                Trả về kết quả kiểm tra:
                {{
                    "is_valid": true,
                    "validation_score": 0.9,
                    "issues": [],
                    "suggestions": [],
                    "recommendations": "Mẫu phù hợp, có thể sử dụng"
                }}"""
    
    @staticmethod
    def template_optimization(template: str, performance_feedback: str) -> str:
        return f"""Tối ưu hóa mẫu câu hỏi
                
                Mẫu hiện tại: {template}
                Phản hồi hiệu suất: {performance_feedback}
                
                Yêu cầu tối ưu hóa:
                1. Phân tích phản hồi hiệu suất
                2. Xác định các điểm cần cải thiện
                3. Đề xuất các tối ưu hóa
                4. Đảm bảo không làm mất tính hiệu quả
                
                Các khía cạnh tối ưu hóa:
                - Cải thiện độ rõ ràng
                - Tăng tính hấp dẫn
                - Tối ưu hóa độ khó
                - Cải thiện cấu trúc
                - Tăng tính linh hoạt
                
                Trả về mẫu đã tối ưu:
                {{
                    "optimized_template": {{
                        "type": "multiple_choice",
                        "pattern": "Mẫu đã tối ưu",
                        "improvements": ["Danh sách cải thiện"],
                        "performance_expected": "Hiệu suất dự kiến"
                    }},
                    "optimization_summary": "Tóm tắt các tối ưu hóa",
                    "expected_improvements": ["Cải thiện dự kiến"]
                }}"""
    
    @staticmethod
    def template_adaptation(source_template: str, target_grade: int, target_subject: str) -> str:
        return f"""Điều chỉnh mẫu câu hỏi cho mục đích khác
                
                Mẫu gốc: {source_template}
                Lớp đích: {target_grade}
                Môn đích: {target_subject}
                
                Yêu cầu điều chỉnh:
                1. Phân tích mẫu gốc
                2. Xác định các yếu tố cần thay đổi
                3. Điều chỉnh cho phù hợp với lớp {target_grade}
                4. Điều chỉnh cho phù hợp với môn {target_subject}
                5. Đảm bảo tính nhất quán
                
                Các điều chỉnh có thể:
                - Thay đổi độ khó
                - Thay đổi từ vựng
                - Thay đổi cấu trúc
                - Thay đổi số lượng đáp án
                - Thay đổi định dạng
                
                Trả về mẫu đã điều chỉnh:
                {{
                    "adapted_template": {{
                        "type": "multiple_choice",
                        "pattern": "Mẫu đã điều chỉnh",
                        "target_grade": {target_grade},
                        "target_subject": "{target_subject}",
                        "adaptations": ["Danh sách điều chỉnh"]
                    }},
                    "adaptation_summary": "Tóm tắt các điều chỉnh",
                    "compatibility_notes": "Ghi chú về tính tương thích"
                }}"""
    
    @staticmethod
    def template_comparison(template1: str, template2: str, criteria: str) -> str:
        return f"""So sánh hai mẫu câu hỏi
                
                Mẫu 1: {template1}
                Mẫu 2: {template2}
                Tiêu chí so sánh: {criteria}
                
                Yêu cầu so sánh:
                1. Phân tích từng mẫu theo tiêu chí
                2. So sánh điểm mạnh, điểm yếu
                3. Đánh giá phù hợp với mục đích sử dụng
                4. Đưa ra khuyến nghị
                
                Các tiêu chí so sánh:
                - Độ rõ ràng
                - Tính linh hoạt
                - Độ khó phù hợp
                - Dễ sử dụng
                - Hiệu quả giáo dục
                
                Trả về kết quả so sánh:
                {{
                    "template1_analysis": {{
                        "strengths": ["Điểm mạnh"],
                        "weaknesses": ["Điểm yếu"],
                        "score": 0.8
                    }},
                    "template2_analysis": {{
                        "strengths": ["Điểm mạnh"],
                        "weaknesses": ["Điểm yếu"],
                        "score": 0.9
                    }},
                    "comparison_summary": "Tóm tắt so sánh",
                    "recommendation": "Mẫu được khuyến nghị",
                    "reasoning": "Lý do khuyến nghị"
                }}"""

