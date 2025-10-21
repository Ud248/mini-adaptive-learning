"""
Script test RAG Tool thủ công
Cho phép nhập skill_name và xem kết quả từ RAG
"""
import sys
import json
from typing import Optional

from agent.tools.rag_tool import RAGTool


def print_section(title: str):
    """In tiêu đề section"""
    print("\n" + "=" * 80)
    print(f"  {title}")
    print("=" * 80)


def print_teacher_context(teacher_context: list):
    """In teacher context (SGV - Sách giáo viên)"""
    print_section(f"TEACHER CONTEXT (SGV) - Tìm thấy {len(teacher_context)} kết quả")
    
    if not teacher_context:
        print("  ❌ Không tìm thấy tài liệu giáo viên nào!")
        return
    
    for idx, item in enumerate(teacher_context, 1):
        print(f"\n📚 Kết quả {idx}:")
        print(f"  🔑 ID: {item.get('id', 'N/A')}")
        
        # In tất cả các trường có trong item
        print(f"  � Các trường có sẵn: {list(item.keys())}")
        
        # Bài học
        lesson = item.get('lesson', '')
        print(f"  � Bài học: {lesson if lesson else '❌ Trống'}")
        
        # Normalized lesson
        norm_lesson = item.get('normalized_lesson', '')
        print(f"  � Normalized: {norm_lesson if norm_lesson else '❌ Không có'}")
        
        # Text/Content
        text = item.get('text', '') or item.get('content', '')
        if text:
            print(f"  📝 Nội dung: {text[:300]}...")
        else:
            print(f"  📝 Nội dung: ❌ Trống")
        
        print(f"  📄 Nguồn: {item.get('source', 'N/A')}")
        
        # Score
        if 'score' in item:
            print(f"  ⭐ Score: {item['score']:.4f}")
        if 'similarity' in item:
            print(f"  ⭐ Similarity: {item['similarity']:.4f}")
        if 'match_type' in item:
            print(f"  🎯 Match type: {item['match_type']}")


def print_textbook_context(textbook_context: list):
    """In textbook context (SGK - Sách giáo khoa)"""
    print_section(f"TEXTBOOK CONTEXT (SGK) - Tìm thấy {len(textbook_context)} kết quả")
    
    if not textbook_context:
        print("  ❌ Không tìm thấy bài tập mẫu nào!")
        return
    
    for idx, item in enumerate(textbook_context, 1):
        print(f"\n📝 Bài tập {idx}:")
        print(f"  🔑 ID: {item.get('id', 'N/A')}")
        
        # In tất cả các trường có trong item để debug
        print(f"  � Các trường có sẵn: {list(item.keys())}")
        
        # Bài học
        lesson = item.get('lesson', '')
        print(f"  � Bài học: {lesson if lesson else '❌ Trống'}")
        
        # Normalized lesson - có thể không có trong kết quả
        norm_lesson = item.get('normalized_lesson', '')
        print(f"  🔍 Normalized: {norm_lesson if norm_lesson else '❌ Không có'}")
        
        # Text (từ RAG tool)
        text = item.get('text', '')
        if text:
            # Text thường có format "Q: ...\nA: ..."
            print(f"  📄 Text (from RAG): {text[:200]}...")
        
        # Câu hỏi và đáp án - có thể là chuỗi rỗng
        question = item.get('question', '')
        answer = item.get('answer', '')
        subject = item.get('subject', '')
        
        if question:
            print(f"  ❓ Câu hỏi: {question}")
        else:
            print(f"  ❓ Câu hỏi: ❌ Trống (có thể chỉ có hình ảnh)")
            
        if answer:
            print(f"  ✅ Đáp án: {answer}")
        else:
            print(f"  ✅ Đáp án: ❌ Trống (có thể chỉ có hình ảnh)")
            
        if subject:
            print(f"  📚 Môn học: {subject}")
        else:
            print(f"  📚 Môn học: ❌ Trống")
        
        print(f"  📄 Nguồn: {item.get('source', 'N/A')}")
        
        # Score từ RAG
        if 'score' in item:
            print(f"  ⭐ Score: {item['score']:.4f}")
        if 'similarity' in item:
            print(f"  ⭐ Similarity: {item['similarity']:.4f}")
        if 'match_type' in item:
            print(f"  🎯 Match type: {item['match_type']}")
        
        # In image nếu có
        if item.get('image_question'):
            images = item['image_question']
            if isinstance(images, list):
                print(f"  🖼️  Hình ảnh câu hỏi ({len(images)} ảnh):")
                for img in images[:3]:  # Chỉ in 3 ảnh đầu
                    print(f"      - {img}")
            else:
                print(f"  🖼️  Hình ảnh câu hỏi: {str(images)[:100]}...")
                
        if item.get('image_answer'):
            images = item['image_answer']
            if isinstance(images, list):
                print(f"  🖼️  Hình ảnh đáp án ({len(images)} ảnh):")
                for img in images[:3]:
                    print(f"      - {img}")
            else:
                print(f"  🖼️  Hình ảnh đáp án: {str(images)[:100]}...")


def print_summary(result: dict):
    """In tóm tắt kết quả"""
    print_section("TÓM TẮT KẾT QUẢ")
    
    teacher_count = len(result.get('teacher_context', []))
    textbook_count = len(result.get('textbook_context', []))
    
    print(f"  📊 Tổng số tài liệu giáo viên: {teacher_count}")
    print(f"  📊 Tổng số bài tập mẫu: {textbook_count}")
    print(f"  📊 Tổng cộng: {teacher_count + textbook_count} kết quả")
    
    if teacher_count == 0 and textbook_count == 0:
        print("\n  ⚠️  CẢNH BÁO: Không tìm thấy kết quả nào!")
        print("  💡 Gợi ý: Kiểm tra lại skill_name hoặc đảm bảo database đã có dữ liệu")


def save_to_json(result: dict, filename: str = "rag_result.json"):
    """Lưu kết quả ra file JSON"""
    try:
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(result, f, ensure_ascii=False, indent=2)
        print(f"\n💾 Đã lưu kết quả vào file: {filename}")
    except Exception as e:
        print(f"\n❌ Lỗi khi lưu file: {e}")


def test_rag_tool(
    skill_name: str,
    grade: int = 1,
    skill: Optional[str] = None,
    topk_sgv: int = 5,
    topk_sgk: int = 20,
    save_json: bool = False
):
    """
    Test RAG tool với skill_name
    
    Args:
        skill_name: Tên kỹ năng/bài học (VD: "Mấy và mấy", "Cộng trong phạm vi 10")
        grade: Lớp (mặc định = 1)
        skill: Mã kỹ năng (tùy chọn)
        topk_sgv: Số lượng tài liệu giáo viên cần lấy (mặc định = 5)
        topk_sgk: Số lượng bài tập mẫu cần lấy (mặc định = 20)
        save_json: Có lưu kết quả ra file JSON không (mặc định = False)
    """
    print_section("TEST RAG TOOL")
    print(f"  🎯 Skill Name: {skill_name}")
    print(f"  📚 Grade: {grade}")
    print(f"  🔑 Skill Code: {skill or 'Auto-detect'}")
    print(f"  📊 Top-K SGV: {topk_sgv}")
    print(f"  📊 Top-K SGK: {topk_sgk}")
    
    try:
        # Khởi tạo RAG tool
        print("\n🔧 Đang khởi tạo RAG Tool...")
        rag_tool = RAGTool()
        
        # Nếu không có skill code, dùng skill_name làm skill code
        if not skill:
            skill = skill_name
        
        # Query RAG
        print(f"🔍 Đang tìm kiếm tài liệu cho '{skill_name}'...")
        result = rag_tool.query(
            grade=grade,
            skill=skill,
            skill_name=skill_name,
            topk_sgv=topk_sgv,
            topk_sgk=topk_sgk
        )
        
        # In kết quả
        print_teacher_context(result.get('teacher_context', []))
        print_textbook_context(result.get('textbook_context', []))
        print_summary(result)
        
        # Lưu JSON nếu cần
        if save_json:
            save_to_json(result)
        
        return result
        
    except Exception as e:
        print(f"\n❌ LỖI: {e}")
        import traceback
        traceback.print_exc()
        return None


def interactive_mode():
    """Chế độ tương tác - cho phép nhập nhiều skill_name"""
    print_section("CHẾĐỘ TƯƠNG TÁC - RAG TOOL TEST")
    print("\n💡 Nhập 'quit' hoặc 'q' để thoát")
    print("💡 Nhập 'save' để lưu kết quả cuối cùng ra JSON\n")
    
    last_result = None
    
    while True:
        print("\n" + "-" * 80)
        skill_name = input("📝 Nhập skill_name (VD: 'Mấy và mấy'): ").strip()
        
        if skill_name.lower() in ['quit', 'q', 'exit']:
            print("👋 Tạm biệt!")
            break
        
        if skill_name.lower() == 'save':
            if last_result:
                save_to_json(last_result)
            else:
                print("❌ Chưa có kết quả nào để lưu!")
            continue
        
        if not skill_name:
            print("⚠️  Vui lòng nhập skill_name!")
            continue
        
        # Tùy chọn nâng cao
        use_advanced = input("🔧 Sử dụng tùy chọn nâng cao? (y/N): ").strip().lower()
        
        if use_advanced == 'y':
            try:
                grade = int(input(f"  📚 Grade (mặc định=1): ").strip() or "1")
                topk_sgv = int(input(f"  📊 Top-K SGV (mặc định=5): ").strip() or "5")
                topk_sgk = int(input(f"  📊 Top-K SGK (mặc định=20): ").strip() or "20")
            except ValueError:
                print("⚠️  Giá trị không hợp lệ, dùng mặc định")
                grade, topk_sgv, topk_sgk = 1, 5, 20
        else:
            grade, topk_sgv, topk_sgk = 1, 5, 20
        
        # Test
        last_result = test_rag_tool(
            skill_name=skill_name,
            grade=grade,
            topk_sgv=topk_sgv,
            topk_sgk=topk_sgk,
            save_json=False
        )


def main():
    """Main function"""
    if len(sys.argv) > 1:
        # Chế độ command-line với argument
        skill_name = ' '.join(sys.argv[1:])
        test_rag_tool(skill_name, save_json=True)
    else:
        # Chế độ tương tác
        interactive_mode()


if __name__ == "__main__":
    main()
