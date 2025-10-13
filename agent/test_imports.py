"""
Test Import Script
=================

Simple script to test if all imports work correctly.
"""

import sys
import os

# Add the project root to the path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

def test_imports():
    """Test all imports."""
    print("🧪 Testing ALQ-Agent imports...")
    print("=" * 50)
    
    # Test prompts imports
    try:
        from agent.prompts import RAGPrompts, GenerationPrompts, ValidationPrompts, TemplatePrompts
        print("✅ Prompts imports: SUCCESS")
    except ImportError as e:
        print(f"❌ Prompts imports: FAILED - {e}")
    
    # Test models imports
    try:
        from agent.models.embedding_model import ALQEmbeddingModel
        print("✅ Models imports: SUCCESS")
    except ImportError as e:
        print(f"❌ Models imports: FAILED - {e}")
    
    # Test tools imports
    try:
        from agent.tools.rag_tool import RAGTool
        from agent.tools.template_tool import TemplateTool
        from agent.tools.question_generation_tool import QuestionGenerationTool
        from agent.tools.validation_tool import ValidationTool
        print("✅ Tools imports: SUCCESS")
    except ImportError as e:
        print(f"❌ Tools imports: FAILED - {e}")
    
    # Test workflow imports
    try:
        from agent.workflow.agent_workflow import AdaptiveLearningAgent
        print("✅ Workflow imports: SUCCESS")
    except ImportError as e:
        print(f"❌ Workflow imports: FAILED - {e}")
    
    # Test main package import
    try:
        from agent import create_alq_agent
        print("✅ Main package import: SUCCESS")
    except ImportError as e:
        print(f"❌ Main package import: FAILED - {e}")
    
    print("\n🎉 Import testing completed!")

if __name__ == "__main__":
    test_imports()
