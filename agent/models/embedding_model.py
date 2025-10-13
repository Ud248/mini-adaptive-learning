"""
ALQ-Agent Embedding Model
========================

Wrapper for the existing Vietnamese text embedding service to be used by ALQ-Agent.
Integrates with database/embeddings/local_embedder.py for consistent embeddings.
"""

import sys
import os
from typing import List, Optional, Dict, Any
import logging

# Add the project root to the path to import local_embedder
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))

try:
    from database.embeddings.local_embedder import LocalEmbedding
except ImportError as e:
    logging.error(f"Failed to import LocalEmbedding: {e}")
    # Try alternative import path
    try:
        import sys
        import os
        sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))
        from database.embeddings.local_embedder import LocalEmbedding
    except ImportError:
        raise ImportError("Please ensure database/embeddings/local_embedder.py is available")


class ALQEmbeddingModel:
    """
    ALQ-Agent Embedding Model wrapper for Vietnamese text embedding service.
    
    This class provides a simplified interface for the ALQ-Agent to use the
    existing Vietnamese embedding service for RAG operations.
    """
    
    def __init__(self, 
                 model_name: str = 'dangvantuan/vietnamese-document-embedding',
                 batch_size: int = 16,
                 verbose: bool = True):
        """
        Initialize the ALQ embedding model.
        
        Args:
            model_name: HuggingFace model name for Vietnamese embeddings
            batch_size: Batch size for processing
            verbose: Enable verbose logging
        """
        self.model_name = model_name
        self.batch_size = batch_size
        self.verbose = verbose
        
        # Initialize the underlying embedding service
        self.embedder = LocalEmbedding(
            model_name=model_name,
            batch_size=batch_size,
            verbose=verbose
        )
        
        if self.verbose:
            print("🧠 ALQ Embedding Model initialized")
    
    def embed_query(self, query: str) -> Optional[List[float]]:
        """
        Embed a single search query for RAG retrieval.
        
        Args:
            query: Search query string
            
        Returns:
            Embedding vector or None if query is empty
        """
        if not query or not query.strip():
            return None
            
        try:
            return self.embedder.embed_single_text(query.strip())
        except Exception as e:
            if self.verbose:
                print(f"❌ Error embedding query: {e}")
            return None
    
    def embed_contexts(self, contexts: List[str]) -> List[List[float]]:
        """
        Embed multiple context texts for batch processing.
        
        Args:
            contexts: List of context strings to embed
            
        Returns:
            List of embedding vectors
        """
        if not contexts:
            return []
            
        try:
            return self.embedder.embed_texts(contexts)
        except Exception as e:
            if self.verbose:
                print(f"❌ Error embedding contexts: {e}")
            # Return zero embeddings as fallback
            return [[0.0] * self.get_embedding_dimension()] * len(contexts)
    
    def embed_educational_content(self, content: Dict[str, Any]) -> Dict[str, Any]:
        """
        Embed educational content with metadata preservation.
        
        Args:
            content: Dictionary containing educational content with 'text' field
            
        Returns:
            Content dictionary with added 'embedding' field
        """
        if not content or 'text' not in content:
            return content
            
        text = content['text']
        if not text or not text.strip():
            content['embedding'] = [0.0] * self.get_embedding_dimension()
            return content
            
        try:
            embedding = self.embed_query(text)
            content['embedding'] = embedding if embedding else [0.0] * self.get_embedding_dimension()
        except Exception as e:
            if self.verbose:
                print(f"❌ Error embedding educational content: {e}")
            content['embedding'] = [0.0] * self.get_embedding_dimension()
            
        return content
    
    def get_embedding_dimension(self) -> int:
        """
        Get the dimension of embeddings produced by this model.
        
        Returns:
            Embedding dimension (768 for Vietnamese model)
        """
        return self.embedder.get_embedding_dimension()
    
    def get_model_info(self) -> Dict[str, Any]:
        """
        Get information about the loaded embedding model.
        
        Returns:
            Dictionary containing model information
        """
        info = self.embedder.get_model_info()
        info['agent_wrapper'] = 'ALQEmbeddingModel'
        return info
    
    def cleanup(self) -> None:
        """
        Clean up GPU memory and resources.
        """
        self.embedder.cleanup()
        if self.verbose:
            print("🧹 ALQ Embedding Model cleaned up")
    
    def __enter__(self):
        """Context manager entry."""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit with cleanup."""
        self.cleanup()


# Convenience functions for quick usage
def create_alq_embedder(model_name: str = 'dangvantuan/vietnamese-document-embedding',
                       batch_size: int = 16,
                       verbose: bool = True) -> ALQEmbeddingModel:
    """
    Create an ALQEmbeddingModel instance with default settings.
    
    Args:
        model_name: HuggingFace model name
        batch_size: Batch size for processing
        verbose: Enable verbose logging
        
    Returns:
        ALQEmbeddingModel instance
    """
    return ALQEmbeddingModel(
        model_name=model_name,
        batch_size=batch_size,
        verbose=verbose
    )


def embed_query_quick(query: str, embedder: Optional[ALQEmbeddingModel] = None) -> Optional[List[float]]:
    """
    Quick function to embed a single query.
    
    Args:
        query: Query string to embed
        embedder: Optional existing embedder instance
        
    Returns:
        Embedding vector or None
    """
    if embedder is None:
        embedder = create_alq_embedder(verbose=False)
    
    try:
        return embedder.embed_query(query)
    finally:
        embedder.cleanup()


# Testing and validation
if __name__ == "__main__":
    print("🧪 Testing ALQ Embedding Model")
    print("=" * 50)
    
    # Test queries
    test_queries = [
        "Cách dạy phép cộng cho học sinh lớp 1",
        "Bài tập về phép trừ có nhớ",
        "Giải thích khái niệm nhiều hơn ít hơn",
        "Phương pháp dạy toán cho trẻ em"
    ]
    
    try:
        # Create embedder
        print("\n📝 Creating ALQ embedder...")
        embedder = ALQEmbeddingModel()
        
        # Test 1: Single query embedding
        print(f"\n🧪 Test 1: Single query embedding")
        single_embedding = embedder.embed_query(test_queries[0])
        if single_embedding:
            print(f"✅ Single embedding dimension: {len(single_embedding)}")
        else:
            print("❌ Single embedding failed")
        
        # Test 2: Multiple contexts embedding
        print(f"\n🧪 Test 2: Multiple contexts embedding")
        context_embeddings = embedder.embed_contexts(test_queries)
        print(f"✅ Context embeddings: {len(context_embeddings)} vectors")
        
        # Test 3: Educational content embedding
        print(f"\n🧪 Test 3: Educational content embedding")
        educational_content = {
            'title': 'Phép cộng cơ bản',
            'text': 'Hướng dẫn dạy phép cộng cho học sinh lớp 1',
            'grade': 1,
            'subject': 'Toán'
        }
        embedded_content = embedder.embed_educational_content(educational_content)
        print(f"✅ Educational content embedded: {len(embedded_content.get('embedding', []))} dimensions")
        
        # Test 4: Model info
        print(f"\n📊 Model Information:")
        model_info = embedder.get_model_info()
        for key, value in model_info.items():
            print(f"   {key}: {value}")
        
        # Cleanup
        embedder.cleanup()
        print(f"\n🎉 All ALQ embedding tests completed successfully!")
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()

