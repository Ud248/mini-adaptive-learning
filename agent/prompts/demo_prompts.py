"""
Demo Prompts Usage
=================

Demonstration of how to use the prompts module in ALQ-Agent.
"""

import sys
import os

# Add the project root to the path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))

from agent.prompts import RAGPrompts, GenerationPrompts, ValidationPrompts, TemplatePrompts


def demo_rag_prompts():
    """Demonstrate RAG prompts usage."""
    print("🔍 Demo: RAG Prompts")
    print("=" * 30)
    
    # Context retrieval
    query = "Cách dạy phép cộng cho học sinh lớp 1"
    grade = 1
    subject = "Toán"
    
    prompt = RAGPrompts.context_retrieval_user(query, grade, subject)
    print(f"Context Retrieval Prompt:")
    print(prompt[:200] + "...")
    print()
    
    # Skill-based retrieval
    skill = "S5"
    skill_name = "Mấy và mấy"
    
    prompt = RAGPrompts.skill_retrieval_user(skill, skill_name, grade, subject)
    print(f"Skill Retrieval Prompt:")
    print(prompt[:200] + "...")
    print()


def demo_generation_prompts():
    """Demonstrate generation prompts usage."""
    print("✏️ Demo: Generation Prompts")
    print("=" * 30)
    
    # Multiple choice generation
    topic = "phép cộng cơ bản"
    grade = 1
    subject = "Toán"
    teacher_context = [
        "Hướng dẫn dạy phép cộng cho học sinh lớp 1",
        "Sử dụng đồ vật để minh họa phép cộng"
    ]
    textbook_context = [
        "2 + 3 = 5",
        "Bài tập: 1 + 4 = ?"
    ]
    
    prompt = GenerationPrompts.multiple_choice_generation(
        topic, grade, subject, teacher_context, textbook_context
    )
    print(f"Multiple Choice Generation Prompt:")
    print(prompt[:300] + "...")
    print()
    
    # Math-specific generation
    skill = "S5"
    prompt = GenerationPrompts.math_specific_generation(
        topic, grade, skill, teacher_context, textbook_context
    )
    print(f"Math-Specific Generation Prompt:")
    print(prompt[:300] + "...")
    print()


def demo_validation_prompts():
    """Demonstrate validation prompts usage."""
    print("✅ Demo: Validation Prompts")
    print("=" * 30)
    
    # Accuracy validation
    question = "2 + 3 = ?"
    answers = [
        {"text": "5", "correct": True},
        {"text": "4", "correct": False},
        {"text": "6", "correct": False},
        {"text": "7", "correct": False}
    ]
    subject = "Toán"
    grade = 1
    
    prompt = ValidationPrompts.accuracy_validation(question, answers, subject, grade)
    print(f"Accuracy Validation Prompt:")
    print(prompt[:300] + "...")
    print()
    
    # Comprehensive validation
    teacher_context = ["Hướng dẫn dạy phép cộng"]
    textbook_context = ["2 + 3 = 5"]
    
    prompt = ValidationPrompts.comprehensive_validation(
        question, answers, grade, subject, teacher_context, textbook_context
    )
    print(f"Comprehensive Validation Prompt:")
    print(prompt[:300] + "...")
    print()


def demo_template_prompts():
    """Demonstrate template prompts usage."""
    print("📋 Demo: Template Prompts")
    print("=" * 30)
    
    # Template selection
    subject = "Toán"
    grade = 1
    topic = "phép cộng"
    difficulty = "easy"
    
    prompt = TemplatePrompts.template_selection(subject, grade, topic, difficulty)
    print(f"Template Selection Prompt:")
    print(prompt[:300] + "...")
    print()
    
    # Template customization
    template = "multiple_choice"
    specific_requirements = "Cần 4 đáp án, phù hợp với lớp 1"
    
    prompt = TemplatePrompts.template_customization(
        template, subject, grade, specific_requirements
    )
    print(f"Template Customization Prompt:")
    print(prompt[:300] + "...")
    print()


def main():
    """Run all prompt demos."""
    print("🧠 ALQ-Agent Prompts Demo")
    print("=" * 50)
    print("This demo shows how to use the prompts module")
    print("for different ALQ-Agent operations.")
    print("=" * 50)
    
    try:
        demo_rag_prompts()
        demo_generation_prompts()
        demo_validation_prompts()
        demo_template_prompts()
        
        print("🎉 All prompt demos completed successfully!")
        print("\nThe prompts module is ready for use in ALQ-Agent tools.")
        
    except Exception as e:
        print(f"❌ Demo failed: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()

