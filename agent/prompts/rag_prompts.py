"""
RAG Tool Prompts
===============

Prompts for context retrieval and query processing in RAG operations.
"""

class RAGPrompts:
    """Collection of prompts for RAG context retrieval and processing"""
    
    # Context retrieval prompts
    CONTEXT_RETRIEVAL_SYSTEM = """Bạn là một chuyên gia giáo dục tiểu học, chuyên về việc truy xuất và phân tích nội dung giáo dục.
                                Nhiệm vụ của bạn là tìm kiếm và trích xuất thông tin phù hợp từ cơ sở dữ liệu giáo dục để hỗ trợ việc tạo câu hỏi học tập."""
    
    @staticmethod
    def context_retrieval_user(query: str, grade: int, subject: str) -> str:
        return f"""Truy vấn: {query}
                Lớp: {grade}
                Môn học: {subject}
                
                Hãy tìm kiếm và trích xuất thông tin phù hợp từ cơ sở dữ liệu giáo dục.
                
                Yêu cầu:
                - Tìm nội dung phù hợp với trình độ lớp {grade}
                - Ưu tiên nội dung liên quan đến môn {subject}
                - Trích xuất cả hướng dẫn giảng dạy và ví dụ thực hành
                - Đảm bảo nội dung chính xác và phù hợp với chương trình học
                
                Trả về kết quả theo định dạng:
                - teacher_context: Hướng dẫn giảng dạy, phương pháp, lý thuyết
                - textbook_context: Ví dụ, bài tập, minh họa thực tế"""
    
    # Skill-based retrieval prompts
    SKILL_RETRIEVAL_SYSTEM = """Bạn là chuyên gia phân tích kỹ năng học tập, chuyên về việc xác định và truy xuất nội dung phù hợp với từng kỹ năng cụ thể.
                              Nhiệm vụ của bạn là tìm kiếm nội dung giáo dục phù hợp với kỹ năng học tập cần cải thiện."""
    
    @staticmethod
    def skill_retrieval_user(skill: str, skill_name: str, grade: int, subject: str) -> str:
        return f"""Kỹ năng: {skill} - {skill_name}
                Lớp: {grade}
                Môn học: {subject}
                
                Tìm kiếm nội dung giáo dục phù hợp để cải thiện kỹ năng này.
                
                Yêu cầu:
                - Tập trung vào kỹ năng cụ thể: {skill_name}
                - Nội dung phù hợp với trình độ lớp {grade}
                - Bao gồm cả lý thuyết và thực hành
                - Ưu tiên nội dung giúp học sinh hiểu và thực hành kỹ năng
                
                Trả về:
                - Phương pháp giảng dạy kỹ năng này
                - Ví dụ minh họa cụ thể
                - Bài tập thực hành phù hợp"""
    
    # Topic-based retrieval prompts
    TOPIC_RETRIEVAL_SYSTEM = """Bạn là chuyên gia chương trình học, chuyên về việc truy xuất nội dung theo chủ đề học tập.
                              Nhiệm vụ của bạn là tìm kiếm nội dung giáo dục phù hợp với chủ đề cụ thể."""
    
    @staticmethod
    def topic_retrieval_user(topic: str, grade: int) -> str:
        return f"""Chủ đề: {topic}
                Lớp: {grade}
                
                Tìm kiếm nội dung giáo dục phù hợp với chủ đề này.
                
                Yêu cầu:
                - Nội dung chính xác về chủ đề: {topic}
                - Phù hợp với trình độ lớp {grade}
                - Bao gồm cả kiến thức cơ bản và nâng cao
                - Có ví dụ thực tế và bài tập ứng dụng
                
                Trả về:
                - Khái niệm cơ bản về chủ đề
                - Phương pháp giảng dạy hiệu quả
                - Ví dụ và bài tập minh họa"""
    
    # Context ranking prompts
    CONTEXT_RANKING_SYSTEM = """Bạn là chuyên gia đánh giá nội dung giáo dục, chuyên về việc xếp hạng và lựa chọn nội dung phù hợp nhất.
                              Nhiệm vụ của bạn là đánh giá và xếp hạng các nội dung giáo dục theo độ phù hợp."""
    
    @staticmethod
    def context_ranking_user(contexts: list, query: str, grade: int) -> str:
        return f"""Truy vấn: {query}
                Lớp: {grade}
                
                Danh sách nội dung cần đánh giá:
                {chr(10).join([f"- {ctx}" for ctx in contexts])}
                
                Hãy đánh giá và xếp hạng các nội dung theo độ phù hợp:
                
                Tiêu chí đánh giá:
                - Độ chính xác về mặt kiến thức
                - Phù hợp với trình độ lớp {grade}
                - Tính thực tiễn và ứng dụng
                - Độ rõ ràng và dễ hiểu
                
                Trả về danh sách xếp hạng từ phù hợp nhất đến ít phù hợp nhất."""
    
    # Context summarization prompts
    CONTEXT_SUMMARIZATION_SYSTEM = """Bạn là chuyên gia tóm tắt nội dung giáo dục, chuyên về việc tóm tắt và tổng hợp thông tin quan trọng.
                                    Nhiệm vụ của bạn là tóm tắt nội dung giáo dục một cách chính xác và súc tích."""
    
    @staticmethod
    def context_summarization_user(contexts: list, focus: str) -> str:
        return f"""Tập trung: {focus}
                
                Nội dung cần tóm tắt:
                {chr(10).join([f"- {ctx}" for ctx in contexts])}
                
                Hãy tóm tắt nội dung theo hướng: {focus}
                
                Yêu cầu:
                - Giữ lại thông tin quan trọng nhất
                - Đảm bảo tính chính xác
                - Sử dụng ngôn ngữ rõ ràng, dễ hiểu
                - Tối đa 200 từ cho mỗi phần tóm tắt
                
                Trả về:
                - Tóm tắt hướng dẫn giảng dạy
                - Tóm tắt ví dụ và bài tập"""

