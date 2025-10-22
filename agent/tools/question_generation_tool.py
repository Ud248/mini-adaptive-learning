import json
import logging
import os
import time
from typing import Any, Dict, List, Optional

from agent.llm.hub import LLMHub
from agent.prompts.generation_prompts import (
    SYSTEM_PROMPT,
    USER_PROMPT_TEMPLATE,
    JSON_FORMAT_INSTRUCTION
)
from agent.tools._json_parser import (
    parse_llm_response,
    validate_question_schema,
    format_context_for_prompt,
    ParseError
)

logger = logging.getLogger(__name__)


class QuestionGenerationTool:
    def __init__(self, hub: LLMHub, config: Optional[Dict[str, Any]] = None) -> None:
        self.hub = hub
        self.cfg = config or self._load_config()
        
        # Configuration parameters
        self.batch_size = self.cfg.get("batch_size", 5)
        self.temperature = self.cfg.get("temperature", 0.3)
        self.max_tokens = self.cfg.get("max_tokens", 2048)
        self.retry_on_parse_error = self.cfg.get("retry_on_parse_error", 2)
        self.enforce_4_answers = self.cfg.get("enforce_4_answers", True)
        
        # Summarization config
        self.enable_teacher_summary = bool(self.cfg.get("enable_teacher_summary", True))
        self.teacher_summary_mode = str(self.cfg.get("teacher_summary_mode", "llm_then_rule")).lower()
        self.teacher_summary_max_tokens = int(self.cfg.get("teacher_summary_max_tokens", 400))
        self.teacher_summary_max_words = int(self.cfg.get("teacher_summary_max_words", 180))
    
    def _load_config(self) -> Dict[str, Any]:
        """Load configuration from configs/agent.yaml"""
        config_path = os.path.join(os.getcwd(), "configs", "agent.yaml")
        try:
            import yaml
            if os.path.isfile(config_path):
                with open(config_path, "r", encoding="utf-8") as f:
                    data = yaml.safe_load(f) or {}
                    return data.get("question_generation", {})
        except Exception as e:
            logger.warning(f"Failed to load config: {e}")
        return {}
    
    def _analyze_context_for_question_type(
        self, 
        teacher_context: List[Dict], 
        textbook_context: List[Dict]
    ) -> str:
        """
        Phân tích context để gợi ý loại câu hỏi phù hợp
        
        Args:
            teacher_context: Context từ SGV
            textbook_context: Context từ SGK
            
        Returns:
            Suggested question type: "multiple_choice" | "true_false" | "fill_blank" | "mixed"
        """
        # Analyze teacher context for pedagogical guidance
        teacher_text = " ".join([ctx.get("text", "") for ctx in teacher_context])
        
        # Analyze textbook context for question patterns
        textbook_text = " ".join([ctx.get("text", "") for ctx in textbook_context])
        
        # Count question patterns
        true_false_indicators = ["đúng", "sai", "không", "có", "phải", "không phải"]
        calculation_indicators = ["tính", "cộng", "trừ", "nhân", "chia", "bằng", "=", "+", "-"]
        shape_indicators = ["hình", "tam giác", "vuông", "tròn", "chữ nhật"]
        
        true_false_count = sum(1 for indicator in true_false_indicators if indicator in teacher_text.lower() or indicator in textbook_text.lower())
        calculation_count = sum(1 for indicator in calculation_indicators if indicator in teacher_text.lower() or indicator in textbook_text.lower())
        shape_count = sum(1 for indicator in shape_indicators if indicator in teacher_text.lower() or indicator in textbook_text.lower())
        
        # Decision logic
        if true_false_count > calculation_count and true_false_count > shape_count:
            return "true_false"
        elif calculation_count > shape_count:
            return "fill_blank"  # Better for calculations
        elif shape_count > 0:
            return "multiple_choice"  # Better for shape recognition
        else:
            return "mixed"  # Let LLM decide
    
    
    # Image handling fully removed

    def generate(self, *, teacher_context: List[Dict[str, Any]], textbook_context: List[Dict[str, Any]], profile_student: Dict[str, Any], constraints: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate questions based on context and constraints
        
        Args:
            teacher_context: Context từ SGV
            textbook_context: Context từ SGK  
            profile_student: Thông tin học sinh
            constraints: Ràng buộc (num_questions, grade, skill, etc.)
            
        Returns:
            Dictionary with generated questions and metadata
        """
        # Parse constraints
        num_questions = constraints.get("num_questions", 5)
        grade = constraints.get("grade", 1)
        skill = constraints.get("skill", "")
        skill_name = constraints.get("skill_name", "")
        
        # Analyze context for question type suggestion
        suggested_type = self._analyze_context_for_question_type(teacher_context, textbook_context)
        
        # Calculate number of batches
        num_batches = (num_questions + self.batch_size - 1) // self.batch_size
        
        # ============================================================
        # SUMMARIZE TEACHER CONTEXT ONLY ONCE (before all batches)
        # ============================================================
        if self.enable_teacher_summary:
            teacher_context_summarized = self._summarize_teacher_context(teacher_context, constraints)
            if not teacher_context_summarized:
                teacher_context_summarized = format_context_for_prompt(teacher_context, [])
            logger.info("✅ Teacher context summarized once for all batches")
        else:
            teacher_context_summarized = format_context_for_prompt(teacher_context, [])
            logger.info("✅ Teacher context formatted (summary disabled)")
        
        all_questions = []
        metadata = {
            "total_questions": num_questions,
            "num_batches": num_batches,
            "suggested_type": suggested_type,
            "has_images": False,
            "image_refs_count": 0
        }
        
        # Generate questions in batches
        for batch_idx in range(num_batches):
            batch_size = min(self.batch_size, num_questions - len(all_questions))
            
            try:
                # Build prompt for this batch (using pre-summarized teacher context)
                prompt = self._build_generation_prompt(
                    teacher_context_summarized=teacher_context_summarized,
                    textbook_context=textbook_context,
                    profile_student=profile_student,
                    constraints=constraints,
                    batch_size=batch_size,
                    suggested_type=suggested_type
                )
                
                # Call LLM with retry logic
                questions = self._generate_batch_with_retry(prompt, batch_idx)
                
                # Attach provenance to each question
                for question in questions:
                    question = self._attach_provenance(
                        question=question,
                        teacher_context=teacher_context,
                        textbook_context=textbook_context,
                        provider_name="llm_hub",  # Will be updated with actual provider
                        temperature=self.temperature,
                        batch_index=batch_idx
                    )
                    
                    all_questions.append(question)
                
                logger.info(f"Generated batch {batch_idx + 1}/{num_batches} with {len(questions)} questions")
                
            except Exception as e:
                logger.error(f"Failed to generate batch {batch_idx + 1}: {e}")
                continue
        
        return {
            "questions": all_questions,
            "metadata": metadata
        }
    
    def _build_generation_prompt(
        self,
        teacher_context_summarized: str,
        textbook_context: List[Dict],
        profile_student: Dict,
        constraints: Dict,
        batch_size: int,
        suggested_type: str,
    ) -> List[Dict[str, str]]:
        """
        Build messages array cho LLM
        
        Args:
            teacher_context_summarized: Teacher context đã được summarize sẵn (string)
            textbook_context: Context từ SGK
            profile_student: Thông tin học sinh
            constraints: Ràng buộc
            batch_size: Số câu hỏi trong batch này
            suggested_type: Loại câu hỏi gợi ý
            
        Returns:
            Messages array cho LLM
        """
        # Use pre-summarized teacher context (no need to summarize again)
        teacher_context_text = teacher_context_summarized
        textbook_context_text = format_context_for_prompt([], textbook_context)
        
        # Get student metrics
        accuracy = profile_student.get("accuracy", 50)
        skipped = profile_student.get("skipped", 10)
        avg_response_time = profile_student.get("avg_response_time", 30)
        
        # Generate difficulty distribution based on accuracy
        if accuracy < 50:
            easy, medium, hard = 60, 30, 10
        elif accuracy < 70:
            easy, medium, hard = 30, 50, 20
        else:
            easy, medium, hard = 20, 30, 50
        
        difficulty_dist = f"• EASY: {easy}% ({int(batch_size*easy/100)} câu)\n• MEDIUM: {medium}% ({int(batch_size*medium/100)} câu)\n• HARD: {hard}% ({int(batch_size*hard/100)} câu)"
        
        # Generate special notes based on other metrics
        notes = []
        if skipped > 30:
            notes.append(f"⚠️ Học sinh bỏ qua {skipped}% câu → Tạo câu RÕ RÀNG hơn")
        if avg_response_time > 60:
            notes.append(f"⚠️ Thời gian {avg_response_time}s/câu → Tạo câu NGẮN GỌN hơn")
        special_notes = "\n".join(notes) if notes else "✓ Không có ghi chú đặc biệt"
        
        # Build user prompt
        user_prompt = USER_PROMPT_TEMPLATE.format(
            batch_size=batch_size,
            skill_name=constraints.get("skill_name", ""),
            accuracy=accuracy,
            answered=profile_student.get("answered", 70),
            skipped=skipped,
            avg_response_time=avg_response_time,
            difficulty_distribution=difficulty_dist,
            special_notes=special_notes,
            teacher_context=teacher_context_text or "(Không có)",
            textbook_context=textbook_context_text or "(Không có)"
        )
        
        # Add type suggestion if not mixed
        if suggested_type != "mixed":
            user_prompt += f"\n\n💡 GỢI Ý: Ưu tiên {suggested_type}"
        
        # Add JSON format instruction (keep for example)
        user_prompt += f"\n\n{JSON_FORMAT_INSTRUCTION}"
        
        return [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt}
        ]

    def _summarize_teacher_context(self, teacher_context: List[Dict], constraints: Dict) -> str:
        if not teacher_context:
            return ""
        mode = self.teacher_summary_mode
        parts = [str(ctx.get("text", "")).strip() for ctx in teacher_context if str(ctx.get("text", "")).strip()]
        merged = "\n\n".join(parts[:3])  # cap 3 blocks
        # Try LLM summary first
        if mode in ("llm_only", "llm_then_rule"):
            try:
                brief_sys = (
                    "Bạn là trợ lý sư phạm. Hãy tóm tắt ngắn gọn 'Mục tiêu - Phương pháp - Bước dạy' "
                    "phù hợp học sinh lớp 1, gạch đầu dòng, tránh ví dụ dài."
                )
                brief_user = (
                    "Tóm tắt các điểm cốt lõi, súc tích, ưu tiên hướng dẫn tính cộng, đặt tính, nhẩm.\n\n"
                    f"Nội dung:\n{merged}\n\nGiới hạn ~{self.teacher_summary_max_words} từ."
                )
                messages = [
                    {"role": "system", "content": brief_sys},
                    {"role": "user", "content": brief_user},
                ]
                
                out, provider_name = self.hub.call(messages=messages, temperature=0.1, max_tokens=self.teacher_summary_max_tokens)
                
                summary = (out or "").strip()
                logger.info(f"📝 Summarized teacher context using {provider_name} ({len(summary)} chars)")
                if summary:
                    return summary
            except Exception as e:
                logger.error(f"Teacher summary failed: {e}")
                if mode == "llm_only":
                    return ""
                # else fallthrough to rule
        # Rule-based fallback
        try:
            import re
            content = " ".join(merged.split())
            sents = re.split(r'(?<=[.!?…])\s+', content)
            keywords = ("mục tiêu","phương pháp","hoạt động","khám phá","đặt tính","tính nhẩm","hướng dẫn")
            scored = []
            for s in sents:
                score = sum(1 for k in keywords if k in s.lower())
                scored.append((score, s))
            scored.sort(key=lambda x: x[0], reverse=True)
            picked = [s for _, s in scored[:6]] or sents[:6]
            short = " ".join(picked)
            words = short.split()
            if len(words) > self.teacher_summary_max_words:
                short = " ".join(words[: self.teacher_summary_max_words]) + "…"
            return short
        except Exception:
            return ""
    
    def _generate_batch_with_retry(self, prompt: List[Dict[str, str]], batch_idx: int) -> List[Dict[str, Any]]:
        """
        Generate batch with retry logic
        
        Args:
            prompt: Messages array
            batch_idx: Batch index for logging
            
        Returns:
            List of generated questions
            
        Raises:
            Exception: If all retries fail
        """
        temperature = self.temperature
        last_error = None
        
        for attempt in range(self.retry_on_parse_error + 1):
            try:
                # Call LLM
                output, provider_name = self.hub.call(
                    messages=prompt,
                    temperature=temperature,
                    max_tokens=self.max_tokens
                )
                
                # Parse response
                data = parse_llm_response(output)
                
                # Validate schema
                if not validate_question_schema(data):
                    raise ParseError("Invalid question schema")
                
                questions = data["questions"]
                
                # Validate answer count based on question type
                if self.enforce_4_answers:
                    for question in questions:
                        question_type = question.get("question_type", "")
                        answer_count = len(question.get("answers", []))
                        
                        if question_type == "true_false":
                            if answer_count != 2:
                                raise ParseError(f"TRUE_FALSE question has {answer_count} answers, expected 2")
                        else:
                            if answer_count != 4:
                                raise ParseError(f"Question has {answer_count} answers, expected 4")
                
                logger.info(f"Successfully generated batch {batch_idx + 1} with {len(questions)} questions using {provider_name}")
                return questions
                
            except Exception as e:
                last_error = e
                logger.warning(f"Batch {batch_idx + 1} attempt {attempt + 1} failed: {e}")
                
                if attempt < self.retry_on_parse_error:
                    # Reduce temperature for retry
                    temperature = max(0.1, temperature - 0.1)
                    time.sleep(0.5)  # Brief delay before retry
                    continue
                else:
                    break
        
        raise Exception(f"Failed to generate batch {batch_idx + 1} after {self.retry_on_parse_error + 1} attempts: {last_error}")
    
    def _attach_provenance(
        self,
        question: Dict,
        teacher_context: List[Dict],
        textbook_context: List[Dict],
        provider_name: str,
        temperature: float,
        batch_index: int
    ) -> Dict:
        """
        Gắn provenance đầy đủ vào question
        
        Args:
            question: Question dictionary
            teacher_context: Context từ SGV
            textbook_context: Context từ SGK
            provider_name: Tên LLM provider
            temperature: Temperature used
            batch_index: Batch index
            
        Returns:
            Question with provenance attached
        """
        # Generate unique question ID
        timestamp = int(time.time() * 1000)  # milliseconds
        question_id = f"q_{timestamp}_{batch_index}_{len(question.get('answers', []))}"
        
        # Build provenance
        provenance = {
            "teacher_context_ids": [ctx.get("id", "") for ctx in teacher_context],
            "textbook_context_ids": [ctx.get("id", "") for ctx in textbook_context],
            "provider": provider_name,
            "temperature": temperature,
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S", time.gmtime()),
            "generation_batch": batch_index,
            "question_id": question_id
        }
        
        # Attach provenance to question
        question["provenance"] = provenance
        question["question_id"] = question_id
        
        return question
    
    # Removed image post-processing


