"""
JSON parsing utilities for LLM responses with fallback strategies.
Handles strict JSON parsing and markdown-wrapped JSON extraction.
"""

import json
import re
from typing import Any, Dict, List, Optional


class ParseError(Exception):
    """Raised when JSON parsing fails after all fallback strategies."""
    pass


def _normalize_parsed_payload(payload: Any) -> Dict[str, Any]:
    """
    Normalize arbitrary parsed JSON into the expected dict shape.
    - If payload is a list → wrap as {"questions": payload}
    - If payload is a dict and already has "questions" → return as-is
    - If payload is a dict without "questions" → try to locate a suitable list value
    """
    # Case 1: top-level array
    if isinstance(payload, list):
        return {"questions": payload}

    # Case 2: dict with questions
    if isinstance(payload, dict):
        if "questions" in payload:
            return payload

        # Heuristic: find a list field that looks like questions
        for key, val in payload.items():
            if isinstance(val, list) and val and all(isinstance(x, dict) for x in val):
                # Check required fields for a question object
                sample = val[0]
                if {
                    "question_text",
                    "question_type",
                    "answers",
                }.issubset(set(sample.keys())):
                    out = dict(payload)
                    out["questions"] = val
                    return out

        # Fallback: add empty questions to keep contract, caller will validate False
        return {**payload, "questions": payload.get("questions", [])}

    # Final fallback for unexpected types
    return {"questions": []}


def parse_llm_response(response: str) -> Dict[str, Any]:
    """
    Parse LLM response with multiple fallback strategies.
    
    Strategy 1: Direct JSON parsing
    Strategy 2: Extract from markdown code blocks
    Strategy 3: Find largest JSON object in text
    
    Args:
        response: Raw LLM response string
        
    Returns:
        Parsed JSON dictionary
        
    Raises:
        ParseError: If all strategies fail
    """
    if not response or not response.strip():
        raise ParseError("Empty response")
    
    # Ensure proper UTF-8 encoding
    try:
        if isinstance(response, bytes):
            response = response.decode('utf-8', errors='replace')
    except:
        pass
    
    # Strategy 1: Direct JSON parsing
    try:
        return _normalize_parsed_payload(json.loads(response.strip()))
    except json.JSONDecodeError:
        pass
    
    # Strategy 2: Extract from markdown code blocks
    try:
        json_text = extract_json_from_markdown(response)
        if json_text:
            return _normalize_parsed_payload(json.loads(json_text))
    except json.JSONDecodeError:
        pass
    
    # Strategy 3: Find largest JSON object
    try:
        json_text = find_largest_json_object(response)
        if json_text:
            return _normalize_parsed_payload(json.loads(json_text))
    except json.JSONDecodeError:
        pass
    
    raise ParseError(f"Failed to parse JSON from response: {response[:200]}...")


def extract_json_from_markdown(text: str) -> Optional[str]:
    """
    Extract JSON from markdown code blocks.
    
    Looks for patterns like:
    ```json
    {...}
    ```
    
    Or:
    ```
    {...}
    ```
    
    Args:
        text: Text that may contain markdown-wrapped JSON
        
    Returns:
        Extracted JSON string or None if not found
    """
    # Pattern 1: ```json ... ```
    pattern1 = r'```json\s*\n(.*?)\n```'
    match1 = re.search(pattern1, text, re.DOTALL | re.IGNORECASE)
    if match1:
        return match1.group(1).strip()
    
    # Pattern 2: ``` ... ``` (generic code block)
    pattern2 = r'```\s*\n(.*?)\n```'
    match2 = re.search(pattern2, text, re.DOTALL)
    if match2:
        content = match2.group(1).strip()
        # Check if it looks like JSON
        if content.startswith('{') and content.endswith('}'):
            return content
    
    return None


def find_largest_json_object(text: str) -> Optional[str]:
    """
    Find the largest JSON object in text by looking for {...} patterns.
    
    Args:
        text: Text that may contain JSON objects
        
    Returns:
        Largest JSON string found or None
    """
    # Find all potential JSON objects
    json_candidates = []
    
    # Look for {...} patterns
    brace_pattern = r'\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}'
    matches = re.finditer(brace_pattern, text, re.DOTALL)
    
    for match in matches:
        candidate = match.group(0)
        try:
            # Try to parse to validate it's JSON
            json.loads(candidate)
            json_candidates.append(candidate)
        except json.JSONDecodeError:
            continue
    
    if not json_candidates:
        return None
    
    # Return the largest valid JSON object
    return max(json_candidates, key=len)


def validate_question_schema(data: Dict[str, Any]) -> bool:
    """
    Validate that parsed data matches expected question schema.
    
    Expected schema:
    {
        "questions": [
            {
                "question_text": str,
                "question_type": str,
                "answers": [
                    {"text": str, "correct": bool},
                    ...
                ],
                "explanation": str,
                "image_question": str (optional)
            }
        ]
    }
    
    Args:
        data: Parsed JSON data
        
    Returns:
        True if schema is valid, False otherwise
    """
    import logging
    logger = logging.getLogger(__name__)
    
    try:
        # Check top-level structure
        if not isinstance(data, dict):
            logger.error(f"Schema validation failed: Data is not a dict, got {type(data)}")
            return False
        
        if "questions" not in data:
            logger.error(f"Schema validation failed: Missing 'questions' field. Keys: {list(data.keys())}")
            return False
        
        questions = data["questions"]
        if not isinstance(questions, list):
            logger.error(f"Schema validation failed: 'questions' is not a list, got {type(questions)}")
            return False
        
        if not questions:  # Empty list is invalid
            logger.error("Schema validation failed: 'questions' is empty")
            return False
        
        # Validate each question
        for i, question in enumerate(questions):
            if not validate_single_question(question):
                logger.error(f"Schema validation failed: Question {i} failed validation: {question}")
                return False
        
        logger.info(f"Schema validation passed: {len(questions)} questions validated")
        return True
        
    except Exception as e:
        logger.error(f"Schema validation error: {e}")
        return False


def validate_single_question(question: Dict[str, Any]) -> bool:
    """
    Validate a single question object.
    
    Args:
        question: Single question dictionary
        
    Returns:
        True if valid, False otherwise
    """
    import logging
    logger = logging.getLogger(__name__)
    
    try:
        # Required fields
        required_fields = ["question_text", "question_type", "answers"]
        for field in required_fields:
            if field not in question:
                logger.error(f"Single question validation failed: Missing required field '{field}'. Available fields: {list(question.keys())}")
                return False
        
        # Validate question_text
        if not isinstance(question["question_text"], str) or not question["question_text"].strip():
            logger.error(f"Single question validation failed: Invalid question_text. Type: {type(question['question_text'])}, Value: {question['question_text']}")
            return False
        
        # Validate question_type
        valid_types = ["multiple_choice", "true_false", "fill_blank"]
        if question["question_type"] not in valid_types:
            logger.error(f"Single question validation failed: Invalid question_type '{question['question_type']}'. Valid types: {valid_types}")
            return False
        
        # Validate answers
        answers = question["answers"]
        if not isinstance(answers, list):
            logger.error(f"Single question validation failed: answers is not a list, got {type(answers)}")
            return False
        
        # Check answer count based on question type
        question_type = question.get("question_type", "")
        if question_type == "true_false":
            if len(answers) != 2:  # TRUE_FALSE must have exactly 2 answers
                logger.error(f"Single question validation failed: TRUE_FALSE question has {len(answers)} answers, expected 2")
                return False
        else:
            if len(answers) != 4:  # MULTIPLE_CHOICE and FILL_BLANK must have exactly 4 answers
                logger.error(f"Single question validation failed: Question has {len(answers)} answers, expected 4")
                return False
        
        correct_count = 0
        for i, answer in enumerate(answers):
            if not isinstance(answer, dict):
                logger.error(f"Single question validation failed: Answer {i} is not a dict, got {type(answer)}")
                return False
            
            if "text" not in answer or "correct" not in answer:
                logger.error(f"Single question validation failed: Answer {i} missing 'text' or 'correct' field. Available: {list(answer.keys())}")
                return False
            
            if not isinstance(answer["text"], str) or not answer["text"].strip():
                logger.error(f"Single question validation failed: Answer {i} text is invalid. Type: {type(answer['text'])}, Value: {answer['text']}")
                return False
            
            if not isinstance(answer["correct"], bool):
                logger.error(f"Single question validation failed: Answer {i} 'correct' is not bool, got {type(answer['correct'])}: {answer['correct']}")
                return False
            
            if answer["correct"]:
                correct_count += 1
        
        if correct_count != 1:  # Must have exactly 1 correct answer
            logger.error(f"Single question validation failed: Found {correct_count} correct answers, expected exactly 1")
            return False
        
        # Validate explanation (optional but if present should be string)
        if "explanation" in question:
            if not isinstance(question["explanation"], str):
                logger.error(f"Single question validation failed: explanation is not string, got {type(question['explanation'])}")
                return False
        
        # Validate image_question (optional but if present should be string or None)
        if "image_question" in question:
            if question["image_question"] is not None and not isinstance(question["image_question"], str):
                logger.error(f"Single question validation failed: image_question is not string or None, got {type(question['image_question'])}")
                return False
        
        return True
        
    except Exception as e:
        logger.error(f"Single question validation error: {e}")
        return False


def extract_questions_from_response(response: str) -> List[Dict[str, Any]]:
    """
    Convenience function to extract and validate questions from LLM response.
    
    Args:
        response: Raw LLM response
        
    Returns:
        List of validated question dictionaries
        
    Raises:
        ParseError: If parsing or validation fails
    """
    data = parse_llm_response(response)
    
    if not validate_question_schema(data):
        raise ParseError("Invalid question schema")
    
    return data["questions"]


def format_context_for_prompt(teacher_context: List[Dict], textbook_context: List[Dict]) -> str:
    """
    Format context data for inclusion in prompts.
    
    Args:
        teacher_context: List of teacher context chunks
        textbook_context: List of textbook context chunks
        
    Returns:
        Formatted string for prompt
    """
    formatted = []
    
    if teacher_context:
        formatted.append("NGỮ CẢNH SƯ PHẠM:")
        for i, ctx in enumerate(teacher_context[:3], 1):  # Limit to top 3
            content = ctx.get("text", "").strip()
            if content:
                formatted.append(f"{i}. {content}")
    
    if textbook_context:
        formatted.append("\nBÀI TẬP MẪU:")
        for i, ctx in enumerate(textbook_context[:5], 1):  # Limit to top 5
            content = ctx.get("text", "").strip()
            if content:
                formatted.append(f"{i}. {content}")
    
    return "\n".join(formatted)


def format_image_references(image_refs: Dict[str, List[Dict]]) -> str:
    """
    Format image references for prompt.
    
    Args:
        image_refs: Dictionary with 'image_dependent' and 'image_independent' lists
        
    Returns:
        Formatted string for prompt
    """
    if not image_refs or (not image_refs.get("image_dependent") and not image_refs.get("image_independent")):
        return "Không có hình ảnh có sẵn."
    
    formatted = []
    
    if image_refs.get("image_dependent"):
        formatted.append("HÌNH ẢNH CẦN THIẾT (phải có hình mới trả lời được):")
        for i, ref in enumerate(image_refs["image_dependent"][:2], 1):  # Limit to 2
            formatted.append(f"- Hình {i}: {ref.get('image_url', '')}")
            formatted.append(f"  Câu gốc: {ref.get('original_question', '')}")
    
    if image_refs.get("image_independent"):
        formatted.append("\nHÌNH ẢNH MINH HỌA (có thể trả lời mà không cần hình):")
        for i, ref in enumerate(image_refs["image_independent"][:2], 1):  # Limit to 2
            formatted.append(f"- Hình {i}: {ref.get('image_url', '')}")
            formatted.append(f"  Câu gốc: {ref.get('original_question', '')}")
    
    return "\n".join(formatted)
