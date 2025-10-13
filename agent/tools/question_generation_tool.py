"""
Question Generation Tool for ALQ-Agent
=====================================

Generates personalized questions using retrieved contexts, templates, and student profiles.
Integrates with LLM services to create educationally sound questions.
"""

import sys
import os
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
import json
import logging
import random
import re

# Add the project root to the path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))

try:
    from .prompts.generation_prompts import GenerationPrompts
except ImportError:
    try:
        from agent.prompts.generation_prompts import GenerationPrompts
    except ImportError:
        GenerationPrompts = None


@dataclass
class StudentProfile:
    """Student profile for question generation."""
    grade: int
    subject: str
    skill: str
    skill_name: str
    low_accuracy_skills: List[str]
    slow_response_skills: List[str]
    difficulty_preference: str = "medium"
    learning_style: Optional[str] = None


@dataclass
class GeneratedQuestion:
    """Generated question structure."""
    grade: int
    skill: str
    skill_name: str
    subject: str
    question: str
    image_question: str
    answers: List[Dict[str, Any]]
    image_answer: str
    explanation: str
    difficulty: str
    template_used: str
    generation_metadata: Dict[str, Any]


class QuestionGenerationTool:
    """
    Question Generation Tool for creating personalized questions.
    
    This tool synthesizes retrieved contexts, templates, and student profiles
    to generate educationally appropriate questions using LLM services.
    """
    
    def __init__(self, 
                 llm_connector: Optional[Any] = None,
                 verbose: bool = True):
        """
        Initialize the Question Generation Tool.
        
        Args:
            llm_connector: LLM connector instance
            verbose: Enable verbose logging
        """
        self.verbose = verbose
        self.llm_connector = llm_connector or self._create_mock_llm()
        
        if self.verbose:
            print("✏️ Question Generation Tool initialized")
    
    def _create_mock_llm(self) -> Any:
        """Create mock LLM connector for development."""
        return MockLLMConnector()
    
    def generate(self, 
                topic: str,
                teacher_context: List[Dict[str, Any]],
                textbook_context: List[Dict[str, Any]],
                template: Any,
                student_profile: StudentProfile) -> GeneratedQuestion:
        """
        Generate a personalized question based on contexts and template.
        
        Args:
            topic: Topic or skill to generate question for
            teacher_context: Pedagogical context from teacher_book
            textbook_context: Content context from textbook
            template: Question template to use
            student_profile: Student profile information
            
        Returns:
            GeneratedQuestion instance
        """
        if self.verbose:
            print(f"🎯 Generating question for topic: {topic}")
            print(f"   Grade: {student_profile.grade}")
            print(f"   Skill: {student_profile.skill}")
            print(f"   Template: {template.type.value if hasattr(template, 'type') else 'unknown'}")
        
        try:
            # Prepare context for generation
            context_data = self._prepare_context_data(
                teacher_context, textbook_context, student_profile
            )
            
            # Generate question based on template type
            if hasattr(template, 'type'):
                if template.type.value == "multiple_choice":
                    question_data = self._generate_multiple_choice(
                        topic, template, context_data, student_profile
                    )
                elif template.type.value == "true_false":
                    question_data = self._generate_true_false(
                        topic, template, context_data, student_profile
                    )
                elif template.type.value == "fill_in_blank":
                    question_data = self._generate_fill_in_blank(
                        topic, template, context_data, student_profile
                    )
                else:
                    # Default to multiple choice
                    question_data = self._generate_multiple_choice(
                        topic, template, context_data, student_profile
                    )
            else:
                # Fallback to basic generation
                question_data = self._generate_basic_question(
                    topic, context_data, student_profile
                )
            
            # Create GeneratedQuestion object
            generated_question = GeneratedQuestion(
                grade=student_profile.grade,
                skill=student_profile.skill,
                skill_name=student_profile.skill_name,
                subject=student_profile.subject,
                question=question_data['question'],
                image_question=question_data.get('image_question', ''),
                answers=question_data['answers'],
                image_answer=question_data.get('image_answer', ''),
                explanation=question_data.get('explanation', ''),
                difficulty=question_data.get('difficulty', student_profile.difficulty_preference),
                template_used=template.type.value if hasattr(template, 'type') else 'unknown',
                generation_metadata={
                    'teacher_context_count': len(teacher_context),
                    'textbook_context_count': len(textbook_context),
                    'generation_method': 'llm_synthesis'
                }
            )
            
            if self.verbose:
                print(f"✅ Question generated successfully")
                print(f"   Question: {generated_question.question[:50]}...")
                print(f"   Answers: {len(generated_question.answers)}")
            
            return generated_question
            
        except Exception as e:
            if self.verbose:
                print(f"❌ Question generation failed: {e}")
            
            # Return fallback question
            return self._create_fallback_question(topic, student_profile)
    
    def _prepare_context_data(self, 
                             teacher_context: List[Dict[str, Any]],
                             textbook_context: List[Dict[str, Any]],
                             student_profile: StudentProfile) -> Dict[str, Any]:
        """Prepare context data for question generation."""
        # Extract relevant content from contexts
        teacher_content = []
        for ctx in teacher_context:
            content = ctx.get('content', '')
            if content:
                teacher_content.append(content)
        
        textbook_content = []
        for ctx in textbook_context:
            content = ctx.get('content', '')
            if content:
                textbook_content.append(content)
        
        return {
            'teacher_guidance': teacher_content,
            'textbook_examples': textbook_content,
            'student_grade': student_profile.grade,
            'subject': student_profile.subject,
            'skill': student_profile.skill,
            'skill_name': student_profile.skill_name
        }
    
    def _generate_multiple_choice(self, 
                                 topic: str,
                                 template: Any,
                                 context_data: Dict[str, Any],
                                 student_profile: StudentProfile) -> Dict[str, Any]:
        """Generate multiple choice question."""
        # Use LLM to generate question content
        prompt = self._create_generation_prompt(topic, template, context_data, "multiple_choice")
        
        # Generate using LLM
        llm_response = self.llm_connector.generate(prompt)
        
        # Parse LLM response
        question_data = self._parse_llm_response(llm_response, "multiple_choice")
        
        # Ensure we have the required structure
        if 'answers' not in question_data:
            question_data['answers'] = self._generate_fallback_answers(topic, student_profile)
        
        # Ensure exactly 4 answers
        answers = question_data['answers']
        if len(answers) != 4:
            answers = self._adjust_answer_count(answers, 4)
        
        question_data['answers'] = answers
        return question_data
    
    def _generate_true_false(self, 
                            topic: str,
                            template: Any,
                            context_data: Dict[str, Any],
                            student_profile: StudentProfile) -> Dict[str, Any]:
        """Generate true/false question."""
        prompt = self._create_generation_prompt(topic, template, context_data, "true_false")
        llm_response = self.llm_connector.generate(prompt)
        question_data = self._parse_llm_response(llm_response, "true_false")
        
        # Ensure we have exactly 2 answers for true/false
        if 'answers' not in question_data or len(question_data['answers']) != 2:
            question_data['answers'] = [
                {"text": "Đúng", "correct": True},
                {"text": "Sai", "correct": False}
            ]
        
        return question_data
    
    def _generate_fill_in_blank(self, 
                               topic: str,
                               template: Any,
                               context_data: Dict[str, Any],
                               student_profile: StudentProfile) -> Dict[str, Any]:
        """Generate fill-in-the-blank question."""
        prompt = self._create_generation_prompt(topic, template, context_data, "fill_in_blank")
        llm_response = self.llm_connector.generate(prompt)
        question_data = self._parse_llm_response(llm_response, "fill_in_blank")
        
        # Ensure we have 4 answer options
        if 'answers' not in question_data:
            question_data['answers'] = self._generate_fallback_answers(topic, student_profile)
        
        answers = question_data['answers']
        if len(answers) != 4:
            answers = self._adjust_answer_count(answers, 4)
        
        question_data['answers'] = answers
        return question_data
    
    def _generate_basic_question(self, 
                               topic: str,
                               context_data: Dict[str, Any],
                               student_profile: StudentProfile) -> Dict[str, Any]:
        """Generate basic question as fallback."""
        # Create a simple question based on the topic
        question = f"Bài tập về {topic} cho học sinh lớp {student_profile.grade}"
        
        # Generate simple answers
        answers = self._generate_fallback_answers(topic, student_profile)
        
        return {
            'question': question,
            'answers': answers,
            'explanation': f"Đây là câu hỏi về {topic} dành cho học sinh lớp {student_profile.grade}",
            'difficulty': student_profile.difficulty_preference
        }
    
    def _create_generation_prompt(self, 
                                 topic: str,
                                 template: Any,
                                 context_data: Dict[str, Any],
                                 question_type: str) -> str:
        """Create prompt for LLM generation using prompts module."""
        if GenerationPrompts:
            # Use prompts from prompts module
            if question_type == "multiple_choice":
                return GenerationPrompts.multiple_choice_generation(
                    topic=topic,
                    grade=context_data['student_grade'],
                    subject=context_data['subject'],
                    teacher_context=context_data['teacher_guidance'],
                    textbook_context=context_data['textbook_examples']
                )
            elif question_type == "true_false":
                return GenerationPrompts.true_false_generation(
                    topic=topic,
                    grade=context_data['student_grade'],
                    subject=context_data['subject'],
                    teacher_context=context_data['teacher_guidance'],
                    textbook_context=context_data['textbook_examples']
                )
            elif question_type == "fill_in_blank":
                return GenerationPrompts.fill_in_blank_generation(
                    topic=topic,
                    grade=context_data['student_grade'],
                    subject=context_data['subject'],
                    teacher_context=context_data['teacher_guidance'],
                    textbook_context=context_data['textbook_examples']
                )
            elif context_data['subject'].lower() in ['toán', 'math']:
                return GenerationPrompts.math_specific_generation(
                    topic=topic,
                    grade=context_data['student_grade'],
                    skill=context_data['skill'],
                    teacher_context=context_data['teacher_guidance'],
                    textbook_context=context_data['textbook_examples']
                )
            elif context_data['subject'].lower() in ['tiếng việt', 'vietnamese']:
                return GenerationPrompts.language_specific_generation(
                    topic=topic,
                    grade=context_data['student_grade'],
                    skill=context_data['skill'],
                    teacher_context=context_data['teacher_guidance'],
                    textbook_context=context_data['textbook_examples']
                )
        
        # Fallback to original prompt if prompts module not available
        prompt = f"""
Tạo câu hỏi {question_type} cho học sinh lớp {context_data['student_grade']} về chủ đề: {topic}

Thông tin học sinh:
- Lớp: {context_data['student_grade']}
- Môn học: {context_data['subject']}
- Kỹ năng: {context_data['skill_name']} ({context_data['skill']})

Hướng dẫn từ giáo viên:
{chr(10).join(context_data['teacher_guidance'][:3])}

Ví dụ từ sách giáo khoa:
{chr(10).join(context_data['textbook_examples'][:3])}

Yêu cầu:
1. Tạo câu hỏi phù hợp với trình độ lớp {context_data['student_grade']}
2. Sử dụng ngôn ngữ đơn giản, dễ hiểu
3. Tạo 4 đáp án cho câu hỏi trắc nghiệm
4. Đảm bảo chỉ có 1 đáp án đúng
5. Thêm giải thích ngắn gọn

Định dạng JSON:
{{
    "question": "Câu hỏi...",
    "answers": [
        {{"text": "Đáp án 1", "correct": true}},
        {{"text": "Đáp án 2", "correct": false}},
        {{"text": "Đáp án 3", "correct": false}},
        {{"text": "Đáp án 4", "correct": false}}
    ],
    "explanation": "Giải thích..."
}}
"""
        return prompt
    
    def _parse_llm_response(self, response: str, question_type: str) -> Dict[str, Any]:
        """Parse LLM response into question data."""
        try:
            # Try to extract JSON from response
            json_match = re.search(r'\{.*\}', response, re.DOTALL)
            if json_match:
                json_str = json_match.group()
                return json.loads(json_str)
        except (json.JSONDecodeError, AttributeError):
            pass
        
        # Fallback parsing
        return {
            'question': response[:200] + "..." if len(response) > 200 else response,
            'answers': [],
            'explanation': "Câu hỏi được tạo tự động"
        }
    
    def _generate_fallback_answers(self, topic: str, student_profile: StudentProfile) -> List[Dict[str, Any]]:
        """Generate fallback answers when LLM fails."""
        # Simple fallback based on topic
        if "cộng" in topic.lower() or "addition" in topic.lower():
            return [
                {"text": "5", "correct": True},
                {"text": "4", "correct": False},
                {"text": "6", "correct": False},
                {"text": "3", "correct": False}
            ]
        elif "trừ" in topic.lower() or "subtraction" in topic.lower():
            return [
                {"text": "3", "correct": True},
                {"text": "2", "correct": False},
                {"text": "4", "correct": False},
                {"text": "1", "correct": False}
            ]
        else:
            return [
                {"text": "Đáp án A", "correct": True},
                {"text": "Đáp án B", "correct": False},
                {"text": "Đáp án C", "correct": False},
                {"text": "Đáp án D", "correct": False}
            ]
    
    def _adjust_answer_count(self, answers: List[Dict[str, Any]], target_count: int) -> List[Dict[str, Any]]:
        """Adjust answer count to target number."""
        if len(answers) == target_count:
            return answers
        
        if len(answers) > target_count:
            # Keep first target_count answers
            return answers[:target_count]
        else:
            # Add more answers to reach target_count
            while len(answers) < target_count:
                answers.append({
                    "text": f"Đáp án {chr(65 + len(answers))}",
                    "correct": False
                })
            return answers
    
    def _create_fallback_question(self, topic: str, student_profile: StudentProfile) -> GeneratedQuestion:
        """Create fallback question when generation fails."""
        return GeneratedQuestion(
            grade=student_profile.grade,
            skill=student_profile.skill,
            skill_name=student_profile.skill_name,
            subject=student_profile.subject,
            question=f"Bài tập về {topic} cho học sinh lớp {student_profile.grade}",
            image_question="",
            answers=self._generate_fallback_answers(topic, student_profile),
            image_answer="",
            explanation=f"Đây là câu hỏi mẫu về {topic}",
            difficulty=student_profile.difficulty_preference,
            template_used="fallback",
            generation_metadata={
                'teacher_context_count': 0,
                'textbook_context_count': 0,
                'generation_method': 'fallback'
            }
        )


class MockLLMConnector:
    """Mock LLM connector for development and testing."""
    
    def __init__(self):
        self.verbose = True
    
    def generate(self, prompt: str) -> str:
        """Mock LLM generation."""
        # Extract topic from prompt
        topic_match = re.search(r'chủ đề: (.+?)\n', prompt)
        topic = topic_match.group(1) if topic_match else "toán học"
        
        # Generate mock response based on topic
        if "cộng" in topic.lower() or "addition" in topic.lower():
            return """
{
    "question": "2 + 3 = ?",
    "answers": [
        {"text": "5", "correct": true},
        {"text": "4", "correct": false},
        {"text": "6", "correct": false},
        {"text": "7", "correct": false}
    ],
    "explanation": "2 cộng 3 bằng 5 theo phép cộng cơ bản."
}
"""
        elif "trừ" in topic.lower() or "subtraction" in topic.lower():
            return """
{
    "question": "5 - 2 = ?",
    "answers": [
        {"text": "3", "correct": true},
        {"text": "2", "correct": false},
        {"text": "4", "correct": false},
        {"text": "1", "correct": false}
    ],
    "explanation": "5 trừ 2 bằng 3 theo phép trừ cơ bản."
}
"""
        else:
            return """
{
    "question": "Câu hỏi mẫu về " + topic,
    "answers": [
        {"text": "Đáp án A", "correct": true},
        {"text": "Đáp án B", "correct": false},
        {"text": "Đáp án C", "correct": false},
        {"text": "Đáp án D", "correct": false}
    ],
    "explanation": "Đây là câu hỏi mẫu."
}
"""


# Convenience functions
def create_question_generation_tool(llm_connector: Optional[Any] = None,
                                   verbose: bool = True) -> QuestionGenerationTool:
    """
    Create a QuestionGenerationTool instance.
    
    Args:
        llm_connector: Optional LLM connector instance
        verbose: Enable verbose logging
        
    Returns:
        QuestionGenerationTool instance
    """
    return QuestionGenerationTool(
        llm_connector=llm_connector,
        verbose=verbose
    )


# Testing and validation
if __name__ == "__main__":
    print("🧪 Testing Question Generation Tool")
    print("=" * 50)
    
    try:
        # Create generation tool
        print("\n📝 Creating question generation tool...")
        generation_tool = QuestionGenerationTool(verbose=True)
        
        # Create test student profile
        student_profile = StudentProfile(
            grade=1,
            subject="Toán",
            skill="S5",
            skill_name="Mấy và mấy",
            low_accuracy_skills=["S5"],
            slow_response_skills=[],
            difficulty_preference="easy"
        )
        
        # Create test contexts
        teacher_context = [
            {"content": "Hướng dẫn dạy phép cộng cho học sinh lớp 1"},
            {"content": "Sử dụng đồ vật để minh họa phép cộng"}
        ]
        
        textbook_context = [
            {"content": "2 + 3 = 5"},
            {"content": "Bài tập: 1 + 4 = ?"}
        ]
        
        # Create test template
        from agent.tools.template_tool import QuestionTemplate, QuestionType, DifficultyLevel
        template = QuestionTemplate(
            type=QuestionType.MULTIPLE_CHOICE,
            pattern="{a} + {b} = ?",
            options_count=4,
            grade_range=(1, 2),
            subjects=["Toán"],
            difficulty=DifficultyLevel.EASY,
            description="Basic addition for Grade 1",
            example={}
        )
        
        # Test 1: Generate multiple choice question
        print(f"\n🧪 Test 1: Generate multiple choice question")
        question = generation_tool.generate(
            topic="phép cộng",
            teacher_context=teacher_context,
            textbook_context=textbook_context,
            template=template,
            student_profile=student_profile
        )
        
        print(f"✅ Generated question:")
        print(f"   Question: {question.question}")
        print(f"   Answers: {len(question.answers)}")
        print(f"   Difficulty: {question.difficulty}")
        print(f"   Template: {question.template_used}")
        
        # Test 2: Generate with different template
        print(f"\n🧪 Test 2: Generate true/false question")
        tf_template = QuestionTemplate(
            type=QuestionType.TRUE_FALSE,
            pattern="{statement}",
            options_count=2,
            grade_range=(1, 2),
            subjects=["Toán"],
            difficulty=DifficultyLevel.EASY,
            description="True/False for Grade 1",
            example={}
        )
        
        tf_question = generation_tool.generate(
            topic="phép cộng",
            teacher_context=teacher_context,
            textbook_context=textbook_context,
            template=tf_template,
            student_profile=student_profile
        )
        
        print(f"✅ Generated T/F question:")
        print(f"   Question: {tf_question.question}")
        print(f"   Answers: {len(tf_question.answers)}")
        
        print(f"\n🎉 All question generation tests completed successfully!")
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
