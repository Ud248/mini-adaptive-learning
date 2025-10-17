"""
Comprehensive tests for QuestionGenerationTool
"""

import json
import pytest
from unittest.mock import Mock, patch, MagicMock
from typing import Dict, List, Any

from agent.tools.question_generation_tool import QuestionGenerationTool
from agent.tools._json_parser import ParseError


class TestQuestionGenerationTool:
    """Test cases for QuestionGenerationTool"""
    
    @pytest.fixture
    def mock_hub(self):
        """Mock LLMHub for testing"""
        hub = Mock()
        hub.call.return_value = (
            '{"questions": [{"question_text": "2 + 3 = 5 đúng hay sai?", "question_type": "true_false", "answers": [{"text": "Đúng", "correct": True}, {"text": "Sai", "correct": False}], "explanation": "2 + 3 = 5 là đúng"}, {"question_text": "Số nào đứng trước số 4?", "question_type": "multiple_choice", "answers": [{"text": "3", "correct": True}, {"text": "2", "correct": False}, {"text": "5", "correct": False}, {"text": "1", "correct": False}], "explanation": "Trước 4 là 3"}, {"question_text": "1 + 1 = 2 đúng hay sai?", "question_type": "true_false", "answers": [{"text": "Đúng", "correct": True}, {"text": "Sai", "correct": False}], "explanation": "1 + 1 = 2 là đúng"}, {"question_text": "Hình tam giác có mấy cạnh?", "question_type": "multiple_choice", "answers": [{"text": "3", "correct": True}, {"text": "4", "correct": False}, {"text": "5", "correct": False}, {"text": "6", "correct": False}], "explanation": "Hình tam giác có 3 cạnh"}]}',
            "test_provider"
        )
        return hub
    
    @pytest.fixture
    def sample_teacher_context(self):
        """Sample teacher context"""
        return [
            {
                "id": "teacher_1",
                "text": "Hướng dẫn dạy phép cộng cho học sinh lớp 1",
                "source": "SGV",
                "lesson": "Phép cộng",
                "score": 0.9
            }
        ]
    
    @pytest.fixture
    def sample_textbook_context(self):
        """Sample textbook context"""
        return [
            {
                "id": "textbook_1",
                "text": "Q: 2 + 3 = mấy?\nA: 5",
                "source": "SGK",
                "lesson": "Phép cộng",
                "score": 0.8,
                "image_question": ""
            }
        ]
    
    @pytest.fixture
    def sample_textbook_context_with_images(self):
        """Sample textbook context with images"""
        return [
            {
                "id": "textbook_1",
                "text": "Q: Đếm số hình vuông trong hình vẽ?\nA: 3",
                "source": "SGK",
                "lesson": "Nhận biết hình",
                "score": 0.8,
                "image_question": "@http://example.com/shapes.png"
            },
            {
                "id": "textbook_2", 
                "text": "Q: Hình tam giác có mấy cạnh?\nA: 3",
                "source": "SGK",
                "lesson": "Nhận biết hình",
                "score": 0.7,
                "image_question": "@http://example.com/triangle.png"
            }
        ]
    
    @pytest.fixture
    def sample_profile_student(self):
        """Sample student profile"""
        return {
            "username": "student1",
            "accuracy": 60,
            "skill_id": "S5"
        }
    
    @pytest.fixture
    def sample_constraints(self):
        """Sample constraints"""
        return {
            "num_questions": 4,  # 2 TRUE_FALSE + 2 MULTIPLE_CHOICE
            "grade": 1,
            "skill": "S5",
            "skill_name": "Phép cộng"
        }
    
    def test_init_with_config(self, mock_hub):
        """Test initialization with custom config"""
        config = {
            "batch_size": 3,
            "temperature": 0.5,
            "max_tokens": 1024
        }
        
        tool = QuestionGenerationTool(mock_hub, config)
        
        assert tool.batch_size == 3
        assert tool.temperature == 0.5
        assert tool.max_tokens == 1024
    
    def test_analyze_context_for_question_type_true_false(self, mock_hub):
        """Test question type analysis for true/false questions"""
        tool = QuestionGenerationTool(mock_hub)
        
        teacher_context = [{"text": "Hướng dẫn dạy câu hỏi đúng sai"}]
        textbook_context = [{"text": "Câu hỏi: 2 + 2 = 4 đúng hay sai?"}]
        
        result = tool._analyze_context_for_question_type(teacher_context, textbook_context)
        assert result == "true_false"
    
    def test_analyze_context_for_question_type_calculation(self, mock_hub):
        """Test question type analysis for calculation questions"""
        tool = QuestionGenerationTool(mock_hub)
        
        teacher_context = [{"text": "Hướng dẫn dạy phép tính"}]
        textbook_context = [{"text": "Tính 3 + 4 = ?"}]
        
        result = tool._analyze_context_for_question_type(teacher_context, textbook_context)
        assert result == "fill_blank"
    
    def test_analyze_context_for_question_type_shapes(self, mock_hub):
        """Test question type analysis for shape questions"""
        tool = QuestionGenerationTool(mock_hub)
        
        teacher_context = [{"text": "Hướng dẫn dạy nhận biết hình"}]
        textbook_context = [{"text": "Hình tam giác có mấy cạnh?"}]
        
        result = tool._analyze_context_for_question_type(teacher_context, textbook_context)
        assert result == "multiple_choice"
    
    
    def test_extract_image_references(self, mock_hub, sample_textbook_context_with_images):
        """Test image reference extraction and classification"""
        tool = QuestionGenerationTool(mock_hub)
        
        result = tool._extract_image_references(sample_textbook_context_with_images)
        
        assert "image_dependent" in result
        assert "image_independent" in result
        assert len(result["image_dependent"]) == 1  # "Đếm số hình vuông"
        assert len(result["image_independent"]) == 1  # "Hình tam giác có mấy cạnh"
        
        # Check dependent reference
        dependent = result["image_dependent"][0]
        assert "Đếm số hình vuông" in dependent["original_question"]
        assert dependent["image_url"] == "@http://example.com/shapes.png"
        
        # Check independent reference
        independent = result["image_independent"][0]
        assert "Hình tam giác có mấy cạnh" in independent["original_question"]
        assert independent["image_url"] == "@http://example.com/triangle.png"
    
    def test_has_image_questions_true(self, mock_hub, sample_textbook_context_with_images):
        """Test image question detection when images are present"""
        tool = QuestionGenerationTool(mock_hub)
        
        result = tool._has_image_questions(sample_textbook_context_with_images)
        assert result is True
    
    def test_has_image_questions_false(self, mock_hub, sample_textbook_context):
        """Test image question detection when no images are present"""
        tool = QuestionGenerationTool(mock_hub)
        
        result = tool._has_image_questions(sample_textbook_context)
        assert result is False
    
    def test_generate_basic(self, mock_hub, sample_teacher_context, sample_textbook_context, sample_profile_student, sample_constraints):
        """Test basic question generation"""
        tool = QuestionGenerationTool(mock_hub)
        
        result = tool.generate(
            teacher_context=sample_teacher_context,
            textbook_context=sample_textbook_context,
            profile_student=sample_profile_student,
            constraints=sample_constraints
        )
        
        assert "questions" in result
        assert "metadata" in result
        assert len(result["questions"]) == 4
        assert result["metadata"]["total_questions"] == 4
        assert result["metadata"]["num_batches"] == 1  # 4 questions / 4 batch_size = 1 batch
    
    def test_answer_count_by_question_type(self, mock_hub, sample_teacher_context, sample_textbook_context, sample_profile_student, sample_constraints):
        """Test that questions have correct number of answers based on type"""
        tool = QuestionGenerationTool(mock_hub)
        
        result = tool.generate(
            teacher_context=sample_teacher_context,
            textbook_context=sample_textbook_context,
            profile_student=sample_profile_student,
            constraints=sample_constraints
        )
        
        # Check that we have both types of questions
        question_types = [q["question_type"] for q in result["questions"]]
        assert "true_false" in question_types, "Should have TRUE_FALSE questions"
        assert "multiple_choice" in question_types, "Should have MULTIPLE_CHOICE questions"
        
        for question in result["questions"]:
            question_type = question["question_type"]
            answer_count = len(question["answers"])
            
            if question_type == "true_false":
                assert answer_count == 2, f"TRUE_FALSE question has {answer_count} answers, expected 2"
            else:  # multiple_choice or fill_blank
                assert answer_count == 4, f"Question has {answer_count} answers, expected 4"
            
            # Check that exactly 1 answer is correct
            correct_count = sum(1 for answer in question["answers"] if answer["correct"])
            assert correct_count == 1
    
    def test_provenance_complete(self, mock_hub, sample_teacher_context, sample_textbook_context, sample_profile_student, sample_constraints):
        """Test that provenance is complete for all questions"""
        tool = QuestionGenerationTool(mock_hub)
        
        result = tool.generate(
            teacher_context=sample_teacher_context,
            textbook_context=sample_textbook_context,
            profile_student=sample_profile_student,
            constraints=sample_constraints
        )
        
        for question in result["questions"]:
            assert "provenance" in question
            provenance = question["provenance"]
            
            # Check required provenance fields
            required_fields = [
                "teacher_context_ids", "teacher_context",
                "textbook_context_ids", "textbook_context", 
                "provider", "temperature", "timestamp",
                "generation_batch", "question_id"
            ]
            
            for field in required_fields:
                assert field in provenance
            
            # Check that context IDs match context lists
            assert len(provenance["teacher_context_ids"]) == len(provenance["teacher_context"])
            assert len(provenance["textbook_context_ids"]) == len(provenance["textbook_context"])
    
    def test_image_question_processing(self, mock_hub, sample_teacher_context, sample_textbook_context_with_images, sample_profile_student, sample_constraints):
        """Test image question processing"""
        tool = QuestionGenerationTool(mock_hub)
        
        result = tool.generate(
            teacher_context=sample_teacher_context,
            textbook_context=sample_textbook_context_with_images,
            profile_student=sample_profile_student,
            constraints=sample_constraints
        )
        
        # Check that metadata indicates images are present
        assert result["metadata"]["has_images"] is True
        assert result["metadata"]["image_refs_count"] > 0
        
        # Check that some questions might have image_question field
        image_questions = [q for q in result["questions"] if q.get("image_question")]
        # Note: This depends on LLM response, so we just check the structure is correct
        for question in image_questions:
            assert isinstance(question["image_question"], str)
    
    def test_batch_generation(self, mock_hub, sample_teacher_context, sample_textbook_context, sample_profile_student):
        """Test that questions are generated in batches"""
        tool = QuestionGenerationTool(mock_hub)
        
        # Mock hub to return different responses for each batch
        mock_hub.call.side_effect = [
            # First batch (4 questions)
            ('{"questions": [{"question_text": "2 + 3 = 5 đúng hay sai?", "question_type": "true_false", "answers": [{"text": "Đúng", "correct": True}, {"text": "Sai", "correct": False}], "explanation": "2 + 3 = 5 là đúng"}, {"question_text": "Số nào đứng trước số 4?", "question_type": "multiple_choice", "answers": [{"text": "3", "correct": True}, {"text": "2", "correct": False}, {"text": "5", "correct": False}, {"text": "1", "correct": False}], "explanation": "Trước 4 là 3"}, {"question_text": "1 + 1 = 2 đúng hay sai?", "question_type": "true_false", "answers": [{"text": "Đúng", "correct": True}, {"text": "Sai", "correct": False}], "explanation": "1 + 1 = 2 là đúng"}, {"question_text": "Hình tam giác có mấy cạnh?", "question_type": "multiple_choice", "answers": [{"text": "3", "correct": True}, {"text": "4", "correct": False}, {"text": "5", "correct": False}, {"text": "6", "correct": False}], "explanation": "Hình tam giác có 3 cạnh"}]}', "test_provider"),
            # Second batch (4 questions)
            ('{"questions": [{"question_text": "3 + 2 = 6 đúng hay sai?", "question_type": "true_false", "answers": [{"text": "Đúng", "correct": False}, {"text": "Sai", "correct": True}], "explanation": "3 + 2 = 5, không phải 6"}, {"question_text": "Số nào đứng sau số 2?", "question_type": "multiple_choice", "answers": [{"text": "3", "correct": True}, {"text": "1", "correct": False}, {"text": "4", "correct": False}, {"text": "5", "correct": False}], "explanation": "Sau 2 là 3"}, {"question_text": "4 + 1 = 5 đúng hay sai?", "question_type": "true_false", "answers": [{"text": "Đúng", "correct": True}, {"text": "Sai", "correct": False}], "explanation": "4 + 1 = 5 là đúng"}, {"question_text": "Hình vuông có mấy cạnh?", "question_type": "multiple_choice", "answers": [{"text": "4", "correct": True}, {"text": "3", "correct": False}, {"text": "5", "correct": False}, {"text": "6", "correct": False}], "explanation": "Hình vuông có 4 cạnh"}]}', "test_provider")
        ]
        
        # Test with 8 questions, batch_size=4 -> should be 2 batches
        constraints = {
            "num_questions": 8,
            "grade": 1,
            "skill": "S5",
            "skill_name": "Test"
        }
        
        result = tool.generate(
            teacher_context=sample_teacher_context,
            textbook_context=sample_textbook_context,
            profile_student=sample_profile_student,
            constraints=constraints
        )
        
        assert len(result["questions"]) == 8
        assert result["metadata"]["num_batches"] == 2  # 8 / 4 = 2 batches
        
        # Check that we have both types of questions
        question_types = [q["question_type"] for q in result["questions"]]
        assert "true_false" in question_types, "Should have TRUE_FALSE questions"
        assert "multiple_choice" in question_types, "Should have MULTIPLE_CHOICE questions"
        
        # Verify hub.call was called 2 times (once per batch)
        assert mock_hub.call.call_count == 2
    
    def test_retry_logic_on_parse_error(self, mock_hub, sample_teacher_context, sample_textbook_context, sample_profile_student, sample_constraints):
        """Test retry logic when JSON parsing fails"""
        tool = QuestionGenerationTool(mock_hub)
        
        # Mock hub to return invalid JSON first, then valid JSON
        mock_hub.call.side_effect = [
            ('{"invalid": json}', "test_provider"),  # Invalid JSON
            ('{"questions": [{"question_text": "2 + 3 = 5 đúng hay sai?", "question_type": "true_false", "answers": [{"text": "Đúng", "correct": True}, {"text": "Sai", "correct": False}], "explanation": "2 + 3 = 5 là đúng"}, {"question_text": "Số nào đứng trước số 4?", "question_type": "multiple_choice", "answers": [{"text": "3", "correct": True}, {"text": "2", "correct": False}, {"text": "5", "correct": False}, {"text": "1", "correct": False}], "explanation": "Trước 4 là 3"}]}', "test_provider")
        ]
        
        result = tool.generate(
            teacher_context=sample_teacher_context,
            textbook_context=sample_textbook_context,
            profile_student=sample_profile_student,
            constraints=sample_constraints
        )
        
        # Should succeed after retry
        assert len(result["questions"]) > 0
        
        # Check that we have both types of questions
        question_types = [q["question_type"] for q in result["questions"]]
        assert "true_false" in question_types, "Should have TRUE_FALSE questions"
        assert "multiple_choice" in question_types, "Should have MULTIPLE_CHOICE questions"
        
        # Should have been called twice (initial + retry)
        assert mock_hub.call.call_count == 2
    
    def test_question_type_selection(self, mock_hub, sample_teacher_context, sample_textbook_context, sample_profile_student, sample_constraints):
        """Test that question type selection works correctly"""
        tool = QuestionGenerationTool(mock_hub)
        
        result = tool.generate(
            teacher_context=sample_teacher_context,
            textbook_context=sample_textbook_context,
            profile_student=sample_profile_student,
            constraints=sample_constraints
        )
        
        # Check that suggested type is in metadata
        assert "suggested_type" in result["metadata"]
        assert result["metadata"]["suggested_type"] in ["multiple_choice", "true_false", "fill_blank", "mixed"]
        
        # Check that we have both types of questions
        question_types = [q["question_type"] for q in result["questions"]]
        assert "true_false" in question_types, "Should have TRUE_FALSE questions"
        assert "multiple_choice" in question_types, "Should have MULTIPLE_CHOICE questions"
    
    def test_error_handling_batch_failure(self, mock_hub, sample_teacher_context, sample_textbook_context, sample_profile_student, sample_constraints):
        """Test error handling when a batch fails completely"""
        tool = QuestionGenerationTool(mock_hub)
        
        # Mock hub to always fail
        mock_hub.call.side_effect = Exception("LLM error")
        
        result = tool.generate(
            teacher_context=sample_teacher_context,
            textbook_context=sample_textbook_context,
            profile_student=sample_profile_student,
            constraints=sample_constraints
        )
        
        # Should return empty questions list but not crash
        assert result["questions"] == []
        assert "metadata" in result
    
    def test_config_loading(self, mock_hub):
        """Test configuration loading from YAML file"""
        with patch('builtins.open', mock_open_yaml_content()):
            tool = QuestionGenerationTool(mock_hub)
            
        # Should use default values if config loading fails
        assert tool.batch_size == 4  # default
        assert tool.temperature == 0.3  # default
        
        # Test that tool can generate questions with both types
        result = tool.generate(
            teacher_context=[{"text": "Test context"}],
            textbook_context=[{"text": "Test context"}],
            profile_student={"username": "test", "accuracy": 50, "skill_id": "S5"},
            constraints={"num_questions": 2, "grade": 1, "skill": "S5", "skill_name": "Test"}
        )
        
        # Check that we have both types of questions
        question_types = [q["question_type"] for q in result["questions"]]
        assert "true_false" in question_types, "Should have TRUE_FALSE questions"
        assert "multiple_choice" in question_types, "Should have MULTIPLE_CHOICE questions"
        
        # Check answer counts by type
        for question in result["questions"]:
            question_type = question["question_type"]
            answer_count = len(question["answers"])
            
            if question_type == "true_false":
                assert answer_count == 2, f"TRUE_FALSE question has {answer_count} answers, expected 2"
            else:  # multiple_choice or fill_blank
                assert answer_count == 4, f"Question has {answer_count} answers, expected 4"
    
    def test_unique_question_ids(self, mock_hub, sample_teacher_context, sample_textbook_context, sample_profile_student, sample_constraints):
        """Test that all questions have unique IDs"""
        tool = QuestionGenerationTool(mock_hub)
        
        result = tool.generate(
            teacher_context=sample_teacher_context,
            textbook_context=sample_textbook_context,
            profile_student=sample_profile_student,
            constraints=sample_constraints
        )
        
        question_ids = [q["question_id"] for q in result["questions"]]
        provenance_ids = [q["provenance"]["question_id"] for q in result["questions"]]
        
        # All question IDs should be unique
        assert len(set(question_ids)) == len(question_ids)
        assert len(set(provenance_ids)) == len(provenance_ids)
        
        # Question ID and provenance question_id should match
        for q in result["questions"]:
            assert q["question_id"] == q["provenance"]["question_id"]
        
        # Check that we have both types of questions
        question_types = [q["question_type"] for q in result["questions"]]
        assert "true_false" in question_types, "Should have TRUE_FALSE questions"
        assert "multiple_choice" in question_types, "Should have MULTIPLE_CHOICE questions"
        
        # Check answer counts by type
        for question in result["questions"]:
            question_type = question["question_type"]
            answer_count = len(question["answers"])
            
            if question_type == "true_false":
                assert answer_count == 2, f"TRUE_FALSE question has {answer_count} answers, expected 2"
            else:  # multiple_choice or fill_blank
                assert answer_count == 4, f"Question has {answer_count} answers, expected 4"


def mock_open_yaml_content():
    """Mock YAML file content for testing"""
    yaml_content = """
question_generation:
  batch_size: 3
  temperature: 0.5
  max_tokens: 1024
  retry_on_parse_error: 1
  enforce_4_answers: true
"""
    return MagicMock(return_value=MagicMock(read=MagicMock(return_value=yaml_content)))


if __name__ == "__main__":
    pytest.main([__file__])
