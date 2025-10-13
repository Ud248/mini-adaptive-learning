"""
ALQ-Agent Demo
==============

Demonstration script for the Adaptive Learning Question Agent.
Shows how to use the complete workflow for generating personalized questions.
"""

import sys
import os
import json
from typing import Dict, Any

# Add the project root to the path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from agent import create_alq_agent


def demo_single_question():
    """Demonstrate single question generation."""
    print("🎯 Demo: Single Question Generation")
    print("=" * 50)
    
    # Create ALQ agent
    print("📝 Creating ALQ agent...")
    agent = create_alq_agent(verbose=True)
    
    # Student profile
    student_profile = {
        'grade': 1,
        'subject': 'Toán',
        'skill': 'S5',
        'skill_name': 'Mấy và mấy',
        'low_accuracy_skills': ['S5'],
        'slow_response_skills': [],
        'difficulty': 'easy'
    }
    
    print(f"\n👤 Student Profile:")
    print(f"   Grade: {student_profile['grade']}")
    print(f"   Subject: {student_profile['subject']}")
    print(f"   Skill: {student_profile['skill']} - {student_profile['skill_name']}")
    print(f"   Weak Skills: {student_profile['low_accuracy_skills']}")
    
    # Generate question
    print(f"\n🚀 Generating question...")
    result = agent.run(student_profile, topic="phép cộng cơ bản")
    
    # Display results
    print(f"\n📊 Results:")
    print(f"   Status: {result.status.value}")
    print(f"   Execution Time: {result.execution_time:.2f}s")
    print(f"   Retry Count: {result.retry_count}")
    
    if result.question:
        print(f"\n❓ Generated Question:")
        print(f"   Question: {result.question.question}")
        print(f"   Subject: {result.question.subject}")
        print(f"   Grade: {result.question.grade}")
        print(f"   Difficulty: {result.question.difficulty}")
        
        print(f"\n📝 Answer Options:")
        for i, answer in enumerate(result.question.answers, 1):
            status = "✓" if answer.get('correct', False) else " "
            print(f"   {i}. {status} {answer.get('text', 'N/A')}")
        
        print(f"\n💡 Explanation:")
        print(f"   {result.question.explanation}")
    
    if result.validation_result:
        print(f"\n✅ Validation Results:")
        print(f"   Status: {result.validation_result.validation_status.value}")
        print(f"   Overall Score: {result.validation_result.overall_score:.2f}")
        print(f"   Valid: {result.validation_result.valid}")
        
        if result.validation_result.feedback:
            print(f"   Feedback: {', '.join(result.validation_result.feedback)}")
    
    if result.error_message:
        print(f"\n❌ Error: {result.error_message}")
    
    # Cleanup
    agent.cleanup()
    
    return result


def demo_batch_questions():
    """Demonstrate batch question generation."""
    print("\n\n🎯 Demo: Batch Question Generation")
    print("=" * 50)
    
    # Create ALQ agent
    print("📝 Creating ALQ agent...")
    agent = create_alq_agent(verbose=True)
    
    # Multiple student profiles
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
            'grade': 1,
            'subject': 'Toán',
            'skill': 'S6',
            'skill_name': 'Phép trừ',
            'low_accuracy_skills': ['S6'],
            'slow_response_skills': [],
            'difficulty': 'medium'
        },
        {
            'grade': 2,
            'subject': 'Toán',
            'skill': 'S7',
            'skill_name': 'Phép nhân',
            'low_accuracy_skills': ['S7'],
            'slow_response_skills': [],
            'difficulty': 'medium'
        }
    ]
    
    print(f"\n👥 Processing {len(student_profiles)} students...")
    
    # Generate questions for all students
    results = agent.run_batch(student_profiles)
    
    # Display batch results
    print(f"\n📊 Batch Results:")
    stats = agent.get_workflow_stats(results)
    for key, value in stats.items():
        print(f"   {key}: {value}")
    
    # Show individual results
    print(f"\n📝 Individual Results:")
    for i, result in enumerate(results, 1):
        print(f"\n   Student {i}:")
        print(f"     Status: {result.status.value}")
        if result.question:
            print(f"     Question: {result.question.question[:50]}...")
            print(f"     Skill: {result.question.skill_name}")
        if result.validation_result:
            print(f"     Validation: {result.validation_result.validation_status.value}")
    
    # Cleanup
    agent.cleanup()
    
    return results


def demo_custom_topic():
    """Demonstrate question generation with custom topic."""
    print("\n\n🎯 Demo: Custom Topic Question Generation")
    print("=" * 50)
    
    # Create ALQ agent
    print("📝 Creating ALQ agent...")
    agent = create_alq_agent(verbose=True)
    
    # Student profile
    student_profile = {
        'grade': 1,
        'subject': 'Toán',
        'skill': 'S8',
        'skill_name': 'So sánh số',
        'low_accuracy_skills': ['S8'],
        'slow_response_skills': [],
        'difficulty': 'medium'
    }
    
    # Custom topic
    custom_topic = "So sánh số lớn hơn, nhỏ hơn, bằng nhau"
    
    print(f"\n👤 Student Profile:")
    print(f"   Grade: {student_profile['grade']}")
    print(f"   Subject: {student_profile['subject']}")
    print(f"   Custom Topic: {custom_topic}")
    
    # Generate question
    print(f"\n🚀 Generating question with custom topic...")
    result = agent.run(student_profile, topic=custom_topic)
    
    # Display results
    print(f"\n📊 Results:")
    print(f"   Status: {result.status.value}")
    print(f"   Execution Time: {result.execution_time:.2f}s")
    
    if result.question:
        print(f"\n❓ Generated Question:")
        print(f"   Question: {result.question.question}")
        print(f"   Template Used: {result.template_used}")
        
        print(f"\n📝 Answer Options:")
        for i, answer in enumerate(result.question.answers, 1):
            status = "✓" if answer.get('correct', False) else " "
            print(f"   {i}. {status} {answer.get('text', 'N/A')}")
    
    if result.rag_result:
        print(f"\n🔍 Context Retrieval:")
        print(f"   Teacher Contexts: {len(result.rag_result.teacher_context)}")
        print(f"   Textbook Contexts: {len(result.rag_result.textbook_context)}")
        print(f"   Total Results: {result.rag_result.total_results}")
        print(f"   Retrieval Time: {result.rag_result.retrieval_time:.2f}s")
    
    # Cleanup
    agent.cleanup()
    
    return result


def main():
    """Run all demos."""
    print("🧠 ALQ-Agent Demonstration")
    print("=" * 60)
    print("This demo shows how to use the Adaptive Learning Question Agent")
    print("to generate personalized questions for students.")
    print("=" * 60)
    
    try:
        # Demo 1: Single question
        result1 = demo_single_question()
        
        # Demo 2: Batch questions
        results2 = demo_batch_questions()
        
        # Demo 3: Custom topic
        result3 = demo_custom_topic()
        
        # Summary
        print("\n\n🎉 Demo Summary")
        print("=" * 50)
        print("✅ Single question generation: Completed")
        print("✅ Batch question generation: Completed")
        print("✅ Custom topic generation: Completed")
        print("\nThe ALQ-Agent is ready for production use!")
        
    except Exception as e:
        print(f"\n❌ Demo failed: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()

