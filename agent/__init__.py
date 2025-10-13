"""
ALQ-Agent Package
================

Adaptive Learning Question Agent for personalized question generation.
"""

__version__ = "1.0.0"
__author__ = "ALQ-Agent Team"

# Import main components
try:
    from .workflow.agent_workflow import AdaptiveLearningAgent, create_alq_agent
    from .tools.rag_tool import RAGTool, create_rag_tool
    from .tools.template_tool import TemplateTool, create_template_tool
    from .tools.question_generation_tool import QuestionGenerationTool, create_question_generation_tool
    from .tools.validation_tool import ValidationTool, create_validation_tool
    from .models.embedding_model import ALQEmbeddingModel, create_alq_embedder
except ImportError as e:
    # Graceful import handling for development
    print(f"Warning: Some ALQ-Agent components not available: {e}")

__all__ = [
    'AdaptiveLearningAgent',
    'create_alq_agent',
    'RAGTool',
    'create_rag_tool',
    'TemplateTool', 
    'create_template_tool',
    'QuestionGenerationTool',
    'create_question_generation_tool',
    'ValidationTool',
    'create_validation_tool',
    'ALQEmbeddingModel',
    'create_alq_embedder'
]

