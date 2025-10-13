"""
Validation Tool for ALQ-Agent
============================

Validates generated questions for accuracy, difficulty, clarity, and educational alignment.
Ensures questions meet quality standards before being presented to students.
"""

import sys
import os
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
import re
import json
import logging
import math

# Add the project root to the path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))

try:
    from .prompts.validation_prompts import ValidationPrompts
except ImportError:
    try:
        from agent.prompts.validation_prompts import ValidationPrompts
    except ImportError:
        ValidationPrompts = None


class ValidationStatus(Enum):
    """Validation status levels."""
    APPROVED = "approved"
    NEEDS_REVISION = "needs_revision"
    REJECTED = "rejected"


class ValidationCriteria(Enum):
    """Validation criteria types."""
    ACCURACY = "accuracy"
    DIFFICULTY = "difficulty"
    CLARITY = "clarity"
    PEDAGOGICAL_ALIGNMENT = "pedagogical_alignment"
    LANGUAGE_APPROPRIATENESS = "language_appropriateness"


@dataclass
class ValidationResult:
    """Validation result structure."""
    valid: bool
    validation_status: ValidationStatus
    overall_score: float
    criteria_scores: Dict[str, float]
    feedback: List[str]
    suggestions: List[str]
    metadata: Dict[str, Any]


class ValidationTool:
    """
    Validation Tool for ensuring question quality.
    
    This tool validates generated questions against multiple criteria including
    accuracy, difficulty, clarity, and educational alignment.
    """
    
    def __init__(self, 
                 llm_connector: Optional[Any] = None,
                 verbose: bool = True):
        """
        Initialize the Validation Tool.
        
        Args:
            llm_connector: LLM connector for advanced validation
            verbose: Enable verbose logging
        """
        self.verbose = verbose
        self.llm_connector = llm_connector or self._create_mock_llm()
        
        # Validation thresholds
        self.thresholds = {
            'approval_score': 0.8,
            'revision_score': 0.6,
            'min_accuracy': 0.9,
            'min_clarity': 0.7,
            'min_pedagogical': 0.7
        }
        
        if self.verbose:
            print("✅ Validation Tool initialized")
    
    def _create_mock_llm(self) -> Any:
        """Create mock LLM connector for development."""
        return MockLLMConnector()
    
    def validate(self, 
                question: Any,
                teacher_context: List[Dict[str, Any]],
                textbook_context: List[Dict[str, Any]]) -> ValidationResult:
        """
        Validate a generated question.
        
        Args:
            question: GeneratedQuestion object to validate
            teacher_context: Pedagogical context for validation
            textbook_context: Content context for validation
            
        Returns:
            ValidationResult with validation details
        """
        if self.verbose:
            print(f"🔍 Validating question: {question.question[:50]}...")
        
        try:
            # Perform validation checks
            criteria_scores = {}
            feedback = []
            suggestions = []
            
            # 1. Accuracy validation
            accuracy_score, accuracy_feedback = self._validate_accuracy(question, textbook_context)
            criteria_scores['accuracy'] = accuracy_score
            feedback.extend(accuracy_feedback)
            
            # 2. Difficulty validation
            difficulty_score, difficulty_feedback = self._validate_difficulty(question)
            criteria_scores['difficulty'] = difficulty_score
            feedback.extend(difficulty_feedback)
            
            # 3. Clarity validation
            clarity_score, clarity_feedback = self._validate_clarity(question)
            criteria_scores['clarity'] = clarity_score
            feedback.extend(clarity_feedback)
            
            # 4. Pedagogical alignment validation
            pedagogical_score, pedagogical_feedback = self._validate_pedagogical_alignment(
                question, teacher_context
            )
            criteria_scores['pedagogical_alignment'] = pedagogical_score
            feedback.extend(pedagogical_feedback)
            
            # 5. Language appropriateness validation
            language_score, language_feedback = self._validate_language_appropriateness(question)
            criteria_scores['language_appropriateness'] = language_score
            feedback.extend(language_feedback)
            
            # Calculate overall score
            overall_score = sum(criteria_scores.values()) / len(criteria_scores)
            
            # Determine validation status
            validation_status = self._determine_validation_status(overall_score, criteria_scores)
            
            # Generate suggestions for improvement
            if validation_status != ValidationStatus.APPROVED:
                suggestions = self._generate_suggestions(criteria_scores, question)
            
            # Create validation result
            result = ValidationResult(
                valid=validation_status == ValidationStatus.APPROVED,
                validation_status=validation_status,
                overall_score=overall_score,
                criteria_scores=criteria_scores,
                feedback=feedback,
                suggestions=suggestions,
                metadata={
                    'validation_timestamp': self._get_timestamp(),
                    'question_grade': question.grade,
                    'question_subject': question.subject,
                    'validation_version': '1.0'
                }
            )
            
            if self.verbose:
                print(f"✅ Validation completed: {validation_status.value}")
                print(f"   Overall score: {overall_score:.2f}")
                print(f"   Criteria scores: {criteria_scores}")
            
            return result
            
        except Exception as e:
            if self.verbose:
                print(f"❌ Validation failed: {e}")
            
            # Return failed validation result
            return ValidationResult(
                valid=False,
                validation_status=ValidationStatus.REJECTED,
                overall_score=0.0,
                criteria_scores={},
                feedback=[f"Validation error: {str(e)}"],
                suggestions=["Fix validation error and retry"],
                metadata={'error': str(e)}
            )
    
    def _validate_accuracy(self, question: Any, textbook_context: List[Dict[str, Any]]) -> Tuple[float, List[str]]:
        """Validate mathematical/factual accuracy using prompts module."""
        if ValidationPrompts and hasattr(self.llm_connector, 'validate_question'):
            # Use LLM-based validation with prompts
            try:
                prompt = ValidationPrompts.accuracy_validation(
                    question=question.question,
                    answers=question.answers,
                    subject=question.subject,
                    grade=question.grade
                )
                
                llm_result = self.llm_connector.validate_question(prompt, "")
                if llm_result and 'accuracy_score' in llm_result:
                    return llm_result['accuracy_score'], [llm_result.get('feedback', '')]
            except Exception as e:
                if self.verbose:
                    print(f"LLM validation failed, using fallback: {e}")
        
        # Fallback to rule-based validation
        score = 1.0
        feedback = []
        
        # Check if question has answers
        if not question.answers or len(question.answers) == 0:
            score = 0.0
            feedback.append("Question has no answers")
            return score, feedback
        
        # Check if exactly one answer is correct
        correct_answers = [ans for ans in question.answers if ans.get('correct', False)]
        if len(correct_answers) != 1:
            score = 0.0
            feedback.append(f"Expected exactly 1 correct answer, found {len(correct_answers)}")
            return score, feedback
        
        # For math questions, validate mathematical accuracy
        if question.subject.lower() in ['toán', 'math', 'mathematics']:
            math_score, math_feedback = self._validate_math_accuracy(question)
            score = min(score, math_score)
            feedback.extend(math_feedback)
        
        # Check against textbook context for factual accuracy
        context_score, context_feedback = self._validate_against_context(question, textbook_context)
        score = min(score, context_score)
        feedback.extend(context_feedback)
        
        if score >= 0.9:
            feedback.append("Question is mathematically/factually accurate")
        
        return score, feedback
    
    def _validate_math_accuracy(self, question: Any) -> Tuple[float, List[str]]:
        """Validate mathematical accuracy for math questions."""
        score = 1.0
        feedback = []
        
        # Extract numbers from question
        numbers = re.findall(r'\d+', question.question)
        
        if len(numbers) >= 2:
            try:
                # Try to evaluate simple math expressions
                if '+' in question.question:
                    a, b = int(numbers[0]), int(numbers[1])
                    correct_answer = a + b
                elif '-' in question.question:
                    a, b = int(numbers[0]), int(numbers[1])
                    correct_answer = a - b
                elif '×' in question.question or '*' in question.question:
                    a, b = int(numbers[0]), int(numbers[1])
                    correct_answer = a * b
                else:
                    # Can't validate, assume correct
                    return score, feedback
                
                # Check if correct answer matches any of the answer options
                correct_answers = [ans for ans in question.answers if ans.get('correct', False)]
                if correct_answers:
                    try:
                        correct_text = correct_answers[0]['text']
                        if str(correct_answer) in correct_text:
                            feedback.append("Mathematical calculation is correct")
                        else:
                            score = 0.5
                            feedback.append(f"Expected answer {correct_answer}, but correct answer is {correct_text}")
                    except (ValueError, KeyError):
                        score = 0.8
                        feedback.append("Could not verify mathematical accuracy")
                
            except (ValueError, IndexError):
                score = 0.8
                feedback.append("Could not parse mathematical expression")
        
        return score, feedback
    
    def _validate_against_context(self, question: Any, context: List[Dict[str, Any]]) -> Tuple[float, List[str]]:
        """Validate question against provided context."""
        score = 1.0
        feedback = []
        
        if not context:
            feedback.append("No context available for validation")
            return score, feedback
        
        # Simple keyword matching
        question_text = question.question.lower()
        context_text = ' '.join([ctx.get('content', '') for ctx in context]).lower()
        
        # Check if question topic appears in context
        topic_keywords = question.skill_name.lower().split()
        matches = sum(1 for keyword in topic_keywords if keyword in context_text)
        
        if matches > 0:
            score = 0.9
            feedback.append("Question aligns with provided context")
        else:
            score = 0.7
            feedback.append("Question topic not clearly found in context")
        
        return score, feedback
    
    def _validate_difficulty(self, question: Any) -> Tuple[float, List[str]]:
        """Validate difficulty appropriateness for grade level."""
        score = 1.0
        feedback = []
        
        grade = question.grade
        question_text = question.question
        
        # Check vocabulary complexity
        complex_words = ['phức tạp', 'phân tích', 'tổng hợp', 'đánh giá', 'so sánh']
        complex_word_count = sum(1 for word in complex_words if word in question_text.lower())
        
        if grade <= 2 and complex_word_count > 0:
            score = 0.6
            feedback.append("Question contains complex vocabulary for grade level")
        elif grade >= 3 and complex_word_count == 0:
            score = 0.8
            feedback.append("Question may be too simple for grade level")
        else:
            feedback.append("Difficulty level appears appropriate")
        
        # Check mathematical complexity
        if question.subject.lower() in ['toán', 'math']:
            numbers = re.findall(r'\d+', question_text)
            if grade == 1 and len(numbers) > 2:
                score = min(score, 0.7)
                feedback.append("Question may be too complex for Grade 1")
            elif grade >= 3 and len(numbers) <= 2:
                score = min(score, 0.8)
                feedback.append("Question may be too simple for grade level")
        
        return score, feedback
    
    def _validate_clarity(self, question: Any) -> Tuple[float, List[str]]:
        """Validate question clarity and readability."""
        score = 1.0
        feedback = []
        
        question_text = question.question
        
        # Check question length
        if len(question_text) < 10:
            score = 0.6
            feedback.append("Question is too short")
        elif len(question_text) > 200:
            score = 0.7
            feedback.append("Question may be too long")
        
        # Check for unclear language
        unclear_phrases = ['có thể', 'có lẽ', 'có thể là', 'có thể không']
        unclear_count = sum(1 for phrase in unclear_phrases if phrase in question_text.lower())
        
        if unclear_count > 0:
            score = min(score, 0.7)
            feedback.append("Question contains unclear language")
        
        # Check for proper question format
        if not question_text.endswith('?'):
            score = min(score, 0.8)
            feedback.append("Question should end with a question mark")
        
        # Check answer options clarity
        for i, answer in enumerate(question.answers):
            if len(answer.get('text', '')) < 1:
                score = min(score, 0.5)
                feedback.append(f"Answer option {i+1} is empty")
        
        if score >= 0.8:
            feedback.append("Question is clear and readable")
        
        return score, feedback
    
    def _validate_pedagogical_alignment(self, question: Any, teacher_context: List[Dict[str, Any]]) -> Tuple[float, List[str]]:
        """Validate pedagogical alignment with teacher guidance."""
        score = 1.0
        feedback = []
        
        if not teacher_context:
            feedback.append("No teacher context available for validation")
            return score, feedback
        
        # Check if question follows pedagogical principles
        context_text = ' '.join([ctx.get('content', '') for ctx in teacher_context]).lower()
        
        # Look for pedagogical keywords
        pedagogical_keywords = ['hướng dẫn', 'phương pháp', 'dạy', 'giải thích', 'minh họa']
        matches = sum(1 for keyword in pedagogical_keywords if keyword in context_text)
        
        if matches > 0:
            score = 0.9
            feedback.append("Question aligns with pedagogical guidance")
        else:
            score = 0.7
            feedback.append("Question may not fully align with pedagogical guidance")
        
        # Check grade appropriateness
        grade_keywords = [f'lớp {question.grade}', f'grade {question.grade}']
        grade_matches = sum(1 for keyword in grade_keywords if keyword in context_text)
        
        if grade_matches > 0:
            feedback.append("Question is appropriate for grade level")
        else:
            score = min(score, 0.8)
            feedback.append("Question grade level not clearly supported by context")
        
        return score, feedback
    
    def _validate_language_appropriateness(self, question: Any) -> Tuple[float, List[str]]:
        """Validate language appropriateness for grade level."""
        score = 1.0
        feedback = []
        
        grade = question.grade
        question_text = question.question.lower()
        
        # Check for age-appropriate vocabulary
        if grade <= 2:
            # Simple vocabulary for early grades
            complex_words = ['phân tích', 'tổng hợp', 'đánh giá', 'phức tạp']
            complex_count = sum(1 for word in complex_words if word in question_text)
            
            if complex_count > 0:
                score = 0.6
                feedback.append("Question contains vocabulary too complex for early grades")
            else:
                feedback.append("Vocabulary is appropriate for grade level")
        
        # Check for proper Vietnamese language usage
        vietnamese_indicators = ['của', 'và', 'hoặc', 'với', 'trong', 'cho']
        vietnamese_count = sum(1 for indicator in vietnamese_indicators if indicator in question_text)
        
        if vietnamese_count > 0:
            feedback.append("Question uses appropriate Vietnamese language")
        else:
            score = min(score, 0.8)
            feedback.append("Question may not use proper Vietnamese language structure")
        
        return score, feedback
    
    def _determine_validation_status(self, overall_score: float, criteria_scores: Dict[str, float]) -> ValidationStatus:
        """Determine validation status based on scores."""
        if overall_score >= self.thresholds['approval_score']:
            return ValidationStatus.APPROVED
        elif overall_score >= self.thresholds['revision_score']:
            return ValidationStatus.NEEDS_REVISION
        else:
            return ValidationStatus.REJECTED
    
    def _generate_suggestions(self, criteria_scores: Dict[str, float], question: Any) -> List[str]:
        """Generate improvement suggestions based on low scores."""
        suggestions = []
        
        for criterion, score in criteria_scores.items():
            if score < 0.7:
                if criterion == 'accuracy':
                    suggestions.append("Review mathematical calculations and verify answer correctness")
                elif criterion == 'difficulty':
                    suggestions.append("Adjust difficulty level to match grade requirements")
                elif criterion == 'clarity':
                    suggestions.append("Simplify language and improve question structure")
                elif criterion == 'pedagogical_alignment':
                    suggestions.append("Align question with teaching methods and curriculum")
                elif criterion == 'language_appropriateness':
                    suggestions.append("Use age-appropriate vocabulary and language structure")
        
        return suggestions
    
    def _get_timestamp(self) -> str:
        """Get current timestamp."""
        import datetime
        return datetime.datetime.now().isoformat()
    
    def validate_batch(self, questions: List[Any], contexts: Dict[str, List[Dict[str, Any]]]) -> List[ValidationResult]:
        """Validate multiple questions in batch."""
        results = []
        
        for question in questions:
            teacher_context = contexts.get('teacher', [])
            textbook_context = contexts.get('textbook', [])
            
            result = self.validate(question, teacher_context, textbook_context)
            results.append(result)
        
        return results
    
    def get_validation_stats(self, results: List[ValidationResult]) -> Dict[str, Any]:
        """Get validation statistics from a batch of results."""
        if not results:
            return {}
        
        total = len(results)
        approved = sum(1 for r in results if r.validation_status == ValidationStatus.APPROVED)
        needs_revision = sum(1 for r in results if r.validation_status == ValidationStatus.NEEDS_REVISION)
        rejected = sum(1 for r in results if r.validation_status == ValidationStatus.REJECTED)
        
        avg_score = sum(r.overall_score for r in results) / total
        
        return {
            'total_questions': total,
            'approved': approved,
            'needs_revision': needs_revision,
            'rejected': rejected,
            'approval_rate': approved / total,
            'average_score': avg_score
        }


class MockLLMConnector:
    """Mock LLM connector for development and testing."""
    
    def __init__(self):
        self.verbose = True
    
    def validate_question(self, question: str, context: str) -> Dict[str, Any]:
        """Mock LLM validation."""
        return {
            'accuracy': 0.9,
            'clarity': 0.8,
            'pedagogical_alignment': 0.85,
            'feedback': 'Question appears well-structured'
        }


# Convenience functions
def create_validation_tool(llm_connector: Optional[Any] = None,
                          verbose: bool = True) -> ValidationTool:
    """
    Create a ValidationTool instance.
    
    Args:
        llm_connector: Optional LLM connector instance
        verbose: Enable verbose logging
        
    Returns:
        ValidationTool instance
    """
    return ValidationTool(
        llm_connector=llm_connector,
        verbose=verbose
    )


# Testing and validation
if __name__ == "__main__":
    print("🧪 Testing Validation Tool")
    print("=" * 50)
    
    try:
        # Create validation tool
        print("\n📝 Creating validation tool...")
        validation_tool = ValidationTool(verbose=True)
        
        # Create test question
        from agent.tools.question_generation_tool import GeneratedQuestion
        
        test_question = GeneratedQuestion(
            grade=1,
            skill="S5",
            skill_name="Mấy và mấy",
            subject="Toán",
            question="2 + 3 = ?",
            image_question="",
            answers=[
                {"text": "5", "correct": True},
                {"text": "4", "correct": False},
                {"text": "6", "correct": False},
                {"text": "7", "correct": False}
            ],
            image_answer="",
            explanation="2 cộng 3 bằng 5 theo phép cộng cơ bản.",
            difficulty="easy",
            template_used="multiple_choice",
            generation_metadata={}
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
        
        # Test 1: Validate good question
        print(f"\n🧪 Test 1: Validate good question")
        result = validation_tool.validate(test_question, teacher_context, textbook_context)
        
        print(f"✅ Validation result:")
        print(f"   Valid: {result.valid}")
        print(f"   Status: {result.validation_status.value}")
        print(f"   Overall score: {result.overall_score:.2f}")
        print(f"   Criteria scores: {result.criteria_scores}")
        print(f"   Feedback: {result.feedback}")
        
        # Test 2: Validate bad question
        print(f"\n🧪 Test 2: Validate bad question")
        bad_question = GeneratedQuestion(
            grade=1,
            skill="S5",
            skill_name="Mấy và mấy",
            subject="Toán",
            question="",  # Empty question
            image_question="",
            answers=[],  # No answers
            image_answer="",
            explanation="",
            difficulty="easy",
            template_used="multiple_choice",
            generation_metadata={}
        )
        
        bad_result = validation_tool.validate(bad_question, teacher_context, textbook_context)
        print(f"✅ Bad question validation:")
        print(f"   Valid: {bad_result.valid}")
        print(f"   Status: {bad_result.validation_status.value}")
        print(f"   Overall score: {bad_result.overall_score:.2f}")
        print(f"   Suggestions: {bad_result.suggestions}")
        
        # Test 3: Batch validation
        print(f"\n🧪 Test 3: Batch validation")
        questions = [test_question, bad_question]
        contexts = {'teacher': teacher_context, 'textbook': textbook_context}
        
        batch_results = validation_tool.validate_batch(questions, contexts)
        stats = validation_tool.get_validation_stats(batch_results)
        
        print(f"✅ Batch validation stats:")
        for key, value in stats.items():
            print(f"   {key}: {value}")
        
        print(f"\n🎉 All validation tool tests completed successfully!")
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
