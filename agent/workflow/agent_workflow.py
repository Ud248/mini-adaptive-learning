"""
ALQ-Agent Workflow
=================

Main workflow orchestrator for the Adaptive Learning Question Agent.
Coordinates all tools to generate, validate, and refine personalized questions.
"""

import sys
import os
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, asdict
import json
import logging
import time
from enum import Enum

# Add the project root to the path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))

try:
    from ..tools.rag_tool import RAGTool, RAGResult
    from ..tools.template_tool import TemplateTool, QuestionTemplate
    from ..tools.question_generation_tool import QuestionGenerationTool, GeneratedQuestion, StudentProfile
    from ..tools.validation_tool import ValidationTool, ValidationResult, ValidationStatus
    from ..models.embedding_model import ALQEmbeddingModel
except ImportError:
    try:
        from agent.tools.rag_tool import RAGTool, RAGResult
        from agent.tools.template_tool import TemplateTool, QuestionTemplate
        from agent.tools.question_generation_tool import QuestionGenerationTool, GeneratedQuestion, StudentProfile
        from agent.tools.validation_tool import ValidationTool, ValidationResult, ValidationStatus
        from agent.models.embedding_model import ALQEmbeddingModel
    except ImportError as e:
        logging.error(f"Failed to import agent tools: {e}")
        # Fallback for development
        RAGTool = None
        TemplateTool = None
        QuestionGenerationTool = None
        ValidationTool = None
        ALQEmbeddingModel = None


class WorkflowStatus(Enum):
    """Workflow execution status."""
    SUCCESS = "success"
    PARTIAL_SUCCESS = "partial_success"
    FAILED = "failed"
    RETRYING = "retrying"


@dataclass
class WorkflowResult:
    """Workflow execution result."""
    status: WorkflowStatus
    question: Optional[GeneratedQuestion]
    validation_result: Optional[ValidationResult]
    rag_result: Optional[RAGResult]
    template_used: Optional[str]
    execution_time: float
    retry_count: int
    error_message: Optional[str]
    metadata: Dict[str, Any]


class AdaptiveLearningAgent:
    """
    Main Adaptive Learning Question Agent.
    
    Orchestrates the complete workflow from context retrieval to question validation.
    """
    
    def __init__(self, 
                 embedding_model: Optional[ALQEmbeddingModel] = None,
                 rag_tool: Optional[RAGTool] = None,
                 template_tool: Optional[TemplateTool] = None,
                 generation_tool: Optional[QuestionGenerationTool] = None,
                 validation_tool: Optional[ValidationTool] = None,
                 verbose: bool = True):
        """
        Initialize the Adaptive Learning Agent.
        
        Args:
            embedding_model: Embedding model instance
            rag_tool: RAG tool instance
            template_tool: Template tool instance
            generation_tool: Question generation tool instance
            validation_tool: Validation tool instance
            verbose: Enable verbose logging
        """
        self.verbose = verbose
        self.max_retries = 2
        
        # Initialize tools
        self.embedding_model = embedding_model or self._create_embedding_model()
        self.rag_tool = rag_tool or self._create_rag_tool()
        self.template_tool = template_tool or self._create_template_tool()
        self.generation_tool = generation_tool or self._create_generation_tool()
        self.validation_tool = validation_tool or self._create_validation_tool()
        
        if self.verbose:
            print("🧠 Adaptive Learning Agent initialized")
            print("   Tools loaded: RAG, Template, Generation, Validation")
    
    def _create_embedding_model(self) -> ALQEmbeddingModel:
        """Create embedding model if not provided."""
        if ALQEmbeddingModel is None:
            raise ImportError("ALQEmbeddingModel not available")
        return ALQEmbeddingModel(verbose=self.verbose)
    
    def _create_rag_tool(self) -> RAGTool:
        """Create RAG tool if not provided."""
        if RAGTool is None:
            raise ImportError("RAGTool not available")
        return RAGTool(embedding_model=self.embedding_model, verbose=self.verbose)
    
    def _create_template_tool(self) -> TemplateTool:
        """Create template tool if not provided."""
        if TemplateTool is None:
            raise ImportError("TemplateTool not available")
        return TemplateTool(verbose=self.verbose)
    
    def _create_generation_tool(self) -> QuestionGenerationTool:
        """Create generation tool if not provided."""
        if QuestionGenerationTool is None:
            raise ImportError("QuestionGenerationTool not available")
        return QuestionGenerationTool(verbose=self.verbose)
    
    def _create_validation_tool(self) -> ValidationTool:
        """Create validation tool if not provided."""
        if ValidationTool is None:
            raise ImportError("ValidationTool not available")
        return ValidationTool(verbose=self.verbose)
    
    def run(self, 
            student_profile: Dict[str, Any],
            topic: Optional[str] = None,
            max_retries: Optional[int] = None) -> WorkflowResult:
        """
        Run the complete question generation workflow.
        
        Args:
            student_profile: Student profile dictionary
            topic: Optional specific topic to focus on
            max_retries: Maximum number of retries (overrides default)
            
        Returns:
            WorkflowResult with complete execution details
        """
        start_time = time.time()
        retry_count = 0
        max_retries = max_retries or self.max_retries
        
        if self.verbose:
            print(f"🚀 Starting ALQ-Agent workflow")
            print(f"   Student: Grade {student_profile.get('grade', 'unknown')}")
            print(f"   Subject: {student_profile.get('subject', 'unknown')}")
            print(f"   Topic: {topic or 'auto-detect'}")
        
        try:
            # Step 1: Prepare student profile
            student = self._prepare_student_profile(student_profile)
            
            # Step 2: Determine topic
            if not topic:
                topic = self._determine_topic(student)
            
            # Step 3: Retrieve contexts
            rag_result = self._retrieve_contexts(topic, student)
            if not rag_result or rag_result.total_results == 0:
                return self._create_failed_result(
                    "No relevant contexts found",
                    start_time, retry_count
                )
            
            # Step 4: Select template
            template = self._select_template(student)
            if not template:
                return self._create_failed_result(
                    "No suitable template found",
                    start_time, retry_count
                )
            
            # Step 5: Generate and validate question
            question, validation_result = self._generate_and_validate(
                topic, rag_result, template, student, max_retries
            )
            
            if not question:
                return self._create_failed_result(
                    "Failed to generate valid question",
                    start_time, retry_count
                )
            
            # Step 6: Create successful result
            execution_time = time.time() - start_time
            status = WorkflowStatus.SUCCESS if validation_result.valid else WorkflowStatus.PARTIAL_SUCCESS
            
            if self.verbose:
                print(f"✅ Workflow completed successfully in {execution_time:.2f}s")
                print(f"   Question: {question.question[:50]}...")
                print(f"   Validation: {validation_result.validation_status.value}")
            
            return WorkflowResult(
                status=status,
                question=question,
                validation_result=validation_result,
                rag_result=rag_result,
                template_used=template.type.value if hasattr(template, 'type') else 'unknown',
                execution_time=execution_time,
                retry_count=retry_count,
                error_message=None,
                metadata={
                    'student_grade': student.grade,
                    'student_subject': student.subject,
                    'topic': topic,
                    'context_sources': rag_result.total_results
                }
            )
            
        except Exception as e:
            execution_time = time.time() - start_time
            error_msg = f"Workflow failed: {str(e)}"
            
            if self.verbose:
                print(f"❌ Workflow failed: {error_msg}")
            
            return WorkflowResult(
                status=WorkflowStatus.FAILED,
                question=None,
                validation_result=None,
                rag_result=None,
                template_used=None,
                execution_time=execution_time,
                retry_count=retry_count,
                error_message=error_msg,
                metadata={'error': str(e)}
            )
    
    def _prepare_student_profile(self, profile_dict: Dict[str, Any]) -> StudentProfile:
        """Convert dictionary to StudentProfile object."""
        return StudentProfile(
            grade=profile_dict.get('grade', 1),
            subject=profile_dict.get('subject', 'Toán'),
            skill=profile_dict.get('skill', 'S1'),
            skill_name=profile_dict.get('skill_name', 'Cơ bản'),
            low_accuracy_skills=profile_dict.get('low_accuracy_skills', []),
            slow_response_skills=profile_dict.get('slow_response_skills', []),
            difficulty_preference=profile_dict.get('difficulty', 'medium'),
            learning_style=profile_dict.get('learning_style')
        )
    
    def _determine_topic(self, student: StudentProfile) -> str:
        """Determine topic based on student profile."""
        if student.low_accuracy_skills:
            skill = student.low_accuracy_skills[0]
            return f"{student.subject} {skill} {student.skill_name}"
        else:
            return f"{student.subject} {student.skill} {student.skill_name}"
    
    def _retrieve_contexts(self, topic: str, student: StudentProfile) -> Optional[RAGResult]:
        """Retrieve relevant contexts using RAG tool."""
        if self.verbose:
            print(f"🔍 Retrieving contexts for: {topic}")
        
        try:
            # Try skill-based retrieval first
            if student.skill:
                rag_result = self.rag_tool.retrieve_by_skill(
                    student.skill, student.grade, student.subject, top_k=5
                )
                if rag_result.total_results > 0:
                    return rag_result
            
            # Fallback to general topic retrieval
            return self.rag_tool.retrieve(topic, top_k=5)
            
        except Exception as e:
            if self.verbose:
                print(f"❌ Context retrieval failed: {e}")
            return None
    
    def _select_template(self, student: StudentProfile) -> Optional[QuestionTemplate]:
        """Select appropriate template for the student."""
        if self.verbose:
            print(f"📋 Selecting template for Grade {student.grade} {student.subject}")
        
        try:
            return self.template_tool.get_template(
                subject=student.subject,
                grade=student.grade,
                difficulty=student.difficulty_preference
            )
        except Exception as e:
            if self.verbose:
                print(f"❌ Template selection failed: {e}")
            return None
    
    def _generate_and_validate(self, 
                              topic: str,
                              rag_result: RAGResult,
                              template: QuestionTemplate,
                              student: StudentProfile,
                              max_retries: int) -> Tuple[Optional[GeneratedQuestion], Optional[ValidationResult]]:
        """Generate and validate question with retries."""
        for attempt in range(max_retries + 1):
            if self.verbose and attempt > 0:
                print(f"🔄 Retry attempt {attempt}/{max_retries}")
            
            try:
                # Generate question
                question = self.generation_tool.generate(
                    topic=topic,
                    teacher_context=rag_result.teacher_context,
                    textbook_context=rag_result.textbook_context,
                    template=template,
                    student_profile=student
                )
                
                if not question:
                    continue
                
                # Validate question
                validation_result = self.validation_tool.validate(
                    question=question,
                    teacher_context=rag_result.teacher_context,
                    textbook_context=rag_result.textbook_context
                )
                
                # Check if validation passed
                if validation_result.valid or validation_result.validation_status == ValidationStatus.APPROVED:
                    return question, validation_result
                
                # If not approved but not rejected, we can still return it
                if validation_result.validation_status != ValidationStatus.REJECTED:
                    return question, validation_result
                
                # If rejected, try again
                if self.verbose:
                    print(f"⚠️ Question rejected, retrying...")
                
            except Exception as e:
                if self.verbose:
                    print(f"❌ Generation attempt {attempt + 1} failed: {e}")
                continue
        
        # All attempts failed
        if self.verbose:
            print(f"❌ All generation attempts failed")
        return None, None
    
    def _create_failed_result(self, 
                             error_message: str, 
                             start_time: float, 
                             retry_count: int) -> WorkflowResult:
        """Create a failed workflow result."""
        execution_time = time.time() - start_time
        
        return WorkflowResult(
            status=WorkflowStatus.FAILED,
            question=None,
            validation_result=None,
            rag_result=None,
            template_used=None,
            execution_time=execution_time,
            retry_count=retry_count,
            error_message=error_message,
            metadata={'error': error_message}
        )
    
    def run_batch(self, 
                  student_profiles: List[Dict[str, Any]],
                  topics: Optional[List[str]] = None) -> List[WorkflowResult]:
        """Run workflow for multiple students."""
        results = []
        
        if self.verbose:
            print(f"🚀 Starting batch workflow for {len(student_profiles)} students")
        
        for i, profile in enumerate(student_profiles):
            topic = topics[i] if topics and i < len(topics) else None
            
            if self.verbose:
                print(f"   Processing student {i+1}/{len(student_profiles)}")
            
            result = self.run(profile, topic)
            results.append(result)
        
        if self.verbose:
            success_count = sum(1 for r in results if r.status == WorkflowStatus.SUCCESS)
            print(f"✅ Batch completed: {success_count}/{len(results)} successful")
        
        return results
    
    def get_workflow_stats(self, results: List[WorkflowResult]) -> Dict[str, Any]:
        """Get workflow statistics from results."""
        if not results:
            return {}
        
        total = len(results)
        successful = sum(1 for r in results if r.status == WorkflowStatus.SUCCESS)
        partial = sum(1 for r in results if r.status == WorkflowStatus.PARTIAL_SUCCESS)
        failed = sum(1 for r in results if r.status == WorkflowStatus.FAILED)
        
        avg_time = sum(r.execution_time for r in results) / total
        avg_retries = sum(r.retry_count for r in results) / total
        
        return {
            'total_workflows': total,
            'successful': successful,
            'partial_success': partial,
            'failed': failed,
            'success_rate': successful / total,
            'average_execution_time': avg_time,
            'average_retries': avg_retries
        }
    
    def cleanup(self):
        """Clean up resources."""
        if hasattr(self.embedding_model, 'cleanup'):
            self.embedding_model.cleanup()
        
        if self.verbose:
            print("🧹 ALQ-Agent cleaned up")


# Convenience functions
def create_alq_agent(embedding_model: Optional[ALQEmbeddingModel] = None,
                    rag_tool: Optional[RAGTool] = None,
                    template_tool: Optional[TemplateTool] = None,
                    generation_tool: Optional[QuestionGenerationTool] = None,
                    validation_tool: Optional[ValidationTool] = None,
                    verbose: bool = True) -> AdaptiveLearningAgent:
    """
    Create an AdaptiveLearningAgent instance.
    
    Args:
        embedding_model: Optional embedding model instance
        rag_tool: Optional RAG tool instance
        template_tool: Optional template tool instance
        generation_tool: Optional generation tool instance
        validation_tool: Optional validation tool instance
        verbose: Enable verbose logging
        
    Returns:
        AdaptiveLearningAgent instance
    """
    return AdaptiveLearningAgent(
        embedding_model=embedding_model,
        rag_tool=rag_tool,
        template_tool=template_tool,
        generation_tool=generation_tool,
        validation_tool=validation_tool,
        verbose=verbose
    )


# Testing and validation
if __name__ == "__main__":
    print("🧪 Testing ALQ-Agent Workflow")
    print("=" * 50)
    
    try:
        # Create ALQ agent
        print("\n📝 Creating ALQ agent...")
        agent = AdaptiveLearningAgent(verbose=True)
        
        # Test student profile
        student_profile = {
            'grade': 1,
            'subject': 'Toán',
            'skill': 'S5',
            'skill_name': 'Mấy và mấy',
            'low_accuracy_skills': ['S5'],
            'slow_response_skills': [],
            'difficulty': 'easy'
        }
        
        # Test 1: Single workflow
        print(f"\n🧪 Test 1: Single workflow execution")
        result = agent.run(student_profile, topic="phép cộng cơ bản")
        
        print(f"✅ Workflow result:")
        print(f"   Status: {result.status.value}")
        print(f"   Execution time: {result.execution_time:.2f}s")
        print(f"   Retry count: {result.retry_count}")
        
        if result.question:
            print(f"   Question: {result.question.question[:50]}...")
            print(f"   Answers: {len(result.question.answers)}")
        
        if result.validation_result:
            print(f"   Validation: {result.validation_result.validation_status.value}")
            print(f"   Overall score: {result.validation_result.overall_score:.2f}")
        
        # Test 2: Batch workflow
        print(f"\n🧪 Test 2: Batch workflow execution")
        batch_profiles = [
            student_profile,
            {
                'grade': 1,
                'subject': 'Toán',
                'skill': 'S6',
                'skill_name': 'Phép trừ',
                'low_accuracy_skills': ['S6'],
                'slow_response_skills': [],
                'difficulty': 'medium'
            }
        ]
        
        batch_results = agent.run_batch(batch_profiles)
        stats = agent.get_workflow_stats(batch_results)
        
        print(f"✅ Batch workflow stats:")
        for key, value in stats.items():
            print(f"   {key}: {value}")
        
        # Cleanup
        agent.cleanup()
        
        print(f"\n🎉 All ALQ-Agent workflow tests completed successfully!")
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()

