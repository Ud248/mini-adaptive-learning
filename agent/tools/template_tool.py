"""
Template Tool for ALQ-Agent
===========================

Provides predefined question templates and formats for different subjects,
grades, and difficulty levels. Supports multiple choice, true/false, and
fill-in-the-blank question types.
"""

from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
import json
import logging

try:
    from .prompts.template_prompts import TemplatePrompts
except ImportError:
    try:
        from agent.prompts.template_prompts import TemplatePrompts
    except ImportError:
        TemplatePrompts = None


class QuestionType(Enum):
    """Supported question types."""
    MULTIPLE_CHOICE = "multiple_choice"
    TRUE_FALSE = "true_false"
    FILL_IN_BLANK = "fill_in_blank"
    MATCHING = "matching"
    SEQUENCE = "sequence"


class DifficultyLevel(Enum):
    """Difficulty levels for questions."""
    EASY = "easy"
    MEDIUM = "medium"
    HARD = "hard"


@dataclass
class QuestionTemplate:
    """Question template structure."""
    type: QuestionType
    pattern: str
    options_count: int
    grade_range: Tuple[int, int]
    subjects: List[str]
    difficulty: DifficultyLevel
    description: str
    example: Dict[str, Any]


class TemplateTool:
    """
    Template Tool for providing question templates and formats.
    
    This tool manages predefined question templates for different subjects,
    grades, and difficulty levels, ensuring consistent question generation.
    """
    
    def __init__(self, verbose: bool = True):
        """
        Initialize the Template Tool.
        
        Args:
            verbose: Enable verbose logging
        """
        self.verbose = verbose
        self.templates = self._initialize_templates()
        
        if self.verbose:
            print("📋 Template Tool initialized")
            print(f"   Available templates: {len(self.templates)}")
    
    def _initialize_templates(self) -> Dict[str, QuestionTemplate]:
        """Initialize the question templates database."""
        templates = {}
        
        # Math templates for Grade 1
        templates["math_grade1_addition"] = QuestionTemplate(
            type=QuestionType.MULTIPLE_CHOICE,
            pattern="{a} + {b} = ?",
            options_count=4,
            grade_range=(1, 2),
            subjects=["Toán"],
            difficulty=DifficultyLevel.EASY,
            description="Basic addition for Grade 1",
            example={
                "question": "2 + 3 = ?",
                "answers": [
                    {"text": "5", "correct": True},
                    {"text": "4", "correct": False},
                    {"text": "6", "correct": False},
                    {"text": "7", "correct": False}
                ]
            }
        )
        
        templates["math_grade1_subtraction"] = QuestionTemplate(
            type=QuestionType.MULTIPLE_CHOICE,
            pattern="{a} - {b} = ?",
            options_count=4,
            grade_range=(1, 2),
            subjects=["Toán"],
            difficulty=DifficultyLevel.EASY,
            description="Basic subtraction for Grade 1",
            example={
                "question": "5 - 2 = ?",
                "answers": [
                    {"text": "3", "correct": True},
                    {"text": "2", "correct": False},
                    {"text": "4", "correct": False},
                    {"text": "1", "correct": False}
                ]
            }
        )
        
        templates["math_grade1_comparison"] = QuestionTemplate(
            type=QuestionType.MULTIPLE_CHOICE,
            pattern="{a} và {b}, số nào {comparison}?",
            options_count=4,
            grade_range=(1, 2),
            subjects=["Toán"],
            difficulty=DifficultyLevel.MEDIUM,
            description="Number comparison for Grade 1",
            example={
                "question": "5 và 3, số nào lớn hơn?",
                "answers": [
                    {"text": "5", "correct": True},
                    {"text": "3", "correct": False},
                    {"text": "Bằng nhau", "correct": False},
                    {"text": "Không so sánh được", "correct": False}
                ]
            }
        )
        
        templates["math_grade1_counting"] = QuestionTemplate(
            type=QuestionType.MULTIPLE_CHOICE,
            pattern="Đếm từ {start} đến {end}, có bao nhiêu số?",
            options_count=4,
            grade_range=(1, 2),
            subjects=["Toán"],
            difficulty=DifficultyLevel.EASY,
            description="Counting practice for Grade 1",
            example={
                "question": "Đếm từ 1 đến 5, có bao nhiêu số?",
                "answers": [
                    {"text": "5", "correct": True},
                    {"text": "4", "correct": False},
                    {"text": "6", "correct": False},
                    {"text": "3", "correct": False}
                ]
            }
        )
        
        # True/False templates
        templates["math_grade1_true_false"] = QuestionTemplate(
            type=QuestionType.TRUE_FALSE,
            pattern="{statement}",
            options_count=2,
            grade_range=(1, 3),
            subjects=["Toán"],
            difficulty=DifficultyLevel.MEDIUM,
            description="True/False questions for Grade 1",
            example={
                "question": "2 + 2 = 4",
                "answers": [
                    {"text": "Đúng", "correct": True},
                    {"text": "Sai", "correct": False}
                ]
            }
        )
        
        # Fill in the blank templates
        templates["math_grade1_fill_blank"] = QuestionTemplate(
            type=QuestionType.FILL_IN_BLANK,
            pattern="{a} + {b} = ___",
            options_count=4,
            grade_range=(1, 2),
            subjects=["Toán"],
            difficulty=DifficultyLevel.EASY,
            description="Fill in the blank for Grade 1",
            example={
                "question": "3 + 2 = ___",
                "answers": [
                    {"text": "5", "correct": True},
                    {"text": "4", "correct": False},
                    {"text": "6", "correct": False},
                    {"text": "1", "correct": False}
                ]
            }
        )
        
        # Vietnamese language templates
        templates["vietnamese_grade1_reading"] = QuestionTemplate(
            type=QuestionType.MULTIPLE_CHOICE,
            pattern="Từ '{word}' có nghĩa là gì?",
            options_count=4,
            grade_range=(1, 2),
            subjects=["Tiếng Việt"],
            difficulty=DifficultyLevel.EASY,
            description="Vietnamese vocabulary for Grade 1",
            example={
                "question": "Từ 'nhà' có nghĩa là gì?",
                "answers": [
                    {"text": "Nơi ở", "correct": True},
                    {"text": "Cây cối", "correct": False},
                    {"text": "Con vật", "correct": False},
                    {"text": "Đồ chơi", "correct": False}
                ]
            }
        )
        
        # Science templates
        templates["science_grade1_animals"] = QuestionTemplate(
            type=QuestionType.MULTIPLE_CHOICE,
            pattern="Con {animal} thuộc nhóm nào?",
            options_count=4,
            grade_range=(1, 2),
            subjects=["Khoa học"],
            difficulty=DifficultyLevel.EASY,
            description="Animal classification for Grade 1",
            example={
                "question": "Con chó thuộc nhóm nào?",
                "answers": [
                    {"text": "Động vật có vú", "correct": True},
                    {"text": "Chim", "correct": False},
                    {"text": "Cá", "correct": False},
                    {"text": "Côn trùng", "correct": False}
                ]
            }
        )
        
        return templates
    
    def get_template(self, 
                    subject: str, 
                    grade: int, 
                    difficulty: str = "medium",
                    question_type: Optional[str] = None) -> Optional[QuestionTemplate]:
        """
        Get a suitable template based on subject, grade, and difficulty.
        
        Args:
            subject: Subject area (e.g., "Toán", "Tiếng Việt")
            grade: Student grade level
            difficulty: Difficulty level ("easy", "medium", "hard")
            question_type: Specific question type (optional)
            
        Returns:
            QuestionTemplate or None if no suitable template found
        """
        if self.verbose:
            print(f"🔍 Finding template for: {subject}, Grade {grade}, {difficulty}")
        
        # Filter templates by criteria
        suitable_templates = []
        
        for template_id, template in self.templates.items():
            # Check subject match
            if subject not in template.subjects:
                continue
            
            # Check grade range
            if not (template.grade_range[0] <= grade <= template.grade_range[1]):
                continue
            
            # Check difficulty
            if template.difficulty.value != difficulty:
                continue
            
            # Check question type if specified
            if question_type and template.type.value != question_type:
                continue
            
            suitable_templates.append((template_id, template))
        
        if not suitable_templates:
            if self.verbose:
                print(f"⚠️ No suitable template found, trying with relaxed criteria")
            # Try with relaxed difficulty
            return self._get_template_relaxed(subject, grade, difficulty, question_type)
        
        # Return the first suitable template
        template_id, template = suitable_templates[0]
        
        if self.verbose:
            print(f"✅ Selected template: {template_id}")
            print(f"   Type: {template.type.value}")
            print(f"   Pattern: {template.pattern}")
        
        return template
    
    def _get_template_relaxed(self, 
                             subject: str, 
                             grade: int, 
                             difficulty: str,
                             question_type: Optional[str] = None) -> Optional[QuestionTemplate]:
        """Get template with relaxed criteria if exact match not found."""
        suitable_templates = []
        
        for template_id, template in self.templates.items():
            # Check subject match
            if subject not in template.subjects:
                continue
            
            # Check grade range
            if not (template.grade_range[0] <= grade <= template.grade_range[1]):
                continue
            
            # Check question type if specified
            if question_type and template.type.value != question_type:
                continue
            
            suitable_templates.append((template_id, template))
        
        if suitable_templates:
            template_id, template = suitable_templates[0]
            if self.verbose:
                print(f"✅ Selected template (relaxed): {template_id}")
            return template
        
        return None
    
    def get_all_templates(self, 
                         subject: Optional[str] = None,
                         grade: Optional[int] = None) -> Dict[str, QuestionTemplate]:
        """
        Get all templates matching the criteria.
        
        Args:
            subject: Filter by subject (optional)
            grade: Filter by grade (optional)
            
        Returns:
            Dictionary of matching templates
        """
        filtered_templates = {}
        
        for template_id, template in self.templates.items():
            # Check subject filter
            if subject and subject not in template.subjects:
                continue
            
            # Check grade filter
            if grade and not (template.grade_range[0] <= grade <= template.grade_range[1]):
                continue
            
            filtered_templates[template_id] = template
        
        return filtered_templates
    
    def get_template_by_id(self, template_id: str) -> Optional[QuestionTemplate]:
        """
        Get a specific template by ID.
        
        Args:
            template_id: Template identifier
            
        Returns:
            QuestionTemplate or None if not found
        """
        return self.templates.get(template_id)
    
    def add_custom_template(self, 
                           template_id: str, 
                           template: QuestionTemplate) -> bool:
        """
        Add a custom template to the database.
        
        Args:
            template_id: Unique identifier for the template
            template: QuestionTemplate instance
            
        Returns:
            True if added successfully, False if ID already exists
        """
        if template_id in self.templates:
            if self.verbose:
                print(f"⚠️ Template ID '{template_id}' already exists")
            return False
        
        self.templates[template_id] = template
        
        if self.verbose:
            print(f"✅ Added custom template: {template_id}")
        
        return True
    
    def get_available_subjects(self) -> List[str]:
        """Get list of available subjects."""
        subjects = set()
        for template in self.templates.values():
            subjects.update(template.subjects)
        return sorted(list(subjects))
    
    def get_available_question_types(self) -> List[str]:
        """Get list of available question types."""
        types = set()
        for template in self.templates.values():
            types.add(template.type.value)
        return sorted(list(types))
    
    def get_template_stats(self) -> Dict[str, Any]:
        """
        Get statistics about available templates.
        
        Returns:
            Dictionary containing template statistics
        """
        stats = {
            'total_templates': len(self.templates),
            'subjects': self.get_available_subjects(),
            'question_types': self.get_available_question_types(),
            'difficulty_levels': [level.value for level in DifficultyLevel],
            'grade_coverage': {
                'min': min(template.grade_range[0] for template in self.templates.values()),
                'max': max(template.grade_range[1] for template in self.templates.values())
            }
        }
        
        # Count by subject
        subject_counts = {}
        for template in self.templates.values():
            for subject in template.subjects:
                subject_counts[subject] = subject_counts.get(subject, 0) + 1
        stats['templates_by_subject'] = subject_counts
        
        # Count by question type
        type_counts = {}
        for template in self.templates.values():
            type_name = template.type.value
            type_counts[type_name] = type_counts.get(type_name, 0) + 1
        stats['templates_by_type'] = type_counts
        
        return stats


# Convenience functions
def create_template_tool(verbose: bool = True) -> TemplateTool:
    """
    Create a TemplateTool instance.
    
    Args:
        verbose: Enable verbose logging
        
    Returns:
        TemplateTool instance
    """
    return TemplateTool(verbose=verbose)


# Testing and validation
if __name__ == "__main__":
    print("🧪 Testing Template Tool")
    print("=" * 50)
    
    try:
        # Create template tool
        print("\n📝 Creating template tool...")
        template_tool = TemplateTool(verbose=True)
        
        # Test 1: Get template for Math Grade 1
        print(f"\n🧪 Test 1: Get template for Math Grade 1")
        template = template_tool.get_template("Toán", 1, "easy")
        if template:
            print(f"✅ Found template: {template.type.value}")
            print(f"   Pattern: {template.pattern}")
            print(f"   Options: {template.options_count}")
        else:
            print("❌ No template found")
        
        # Test 2: Get template with specific type
        print(f"\n🧪 Test 2: Get multiple choice template")
        mc_template = template_tool.get_template("Toán", 1, "easy", "multiple_choice")
        if mc_template:
            print(f"✅ Found MC template: {mc_template.description}")
        else:
            print("❌ No MC template found")
        
        # Test 3: Get all templates for a subject
        print(f"\n🧪 Test 3: Get all Math templates")
        math_templates = template_tool.get_all_templates(subject="Toán")
        print(f"✅ Found {len(math_templates)} Math templates")
        for template_id, template in math_templates.items():
            print(f"   {template_id}: {template.description}")
        
        # Test 4: Template statistics
        print(f"\n📊 Template Statistics:")
        stats = template_tool.get_template_stats()
        for key, value in stats.items():
            print(f"   {key}: {value}")
        
        # Test 5: Available subjects and types
        print(f"\n📚 Available subjects: {template_tool.get_available_subjects()}")
        print(f"📝 Available question types: {template_tool.get_available_question_types()}")
        
        print(f"\n🎉 All template tool tests completed successfully!")
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
