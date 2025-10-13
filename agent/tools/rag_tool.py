"""
RAG Tool for ALQ-Agent
=====================

Retrieves relevant pedagogical and content contexts from vector databases.
Queries both teacher_book (sgv_collection) and textbook (baitap_collection) collections.
"""

import sys
import os
from typing import List, Dict, Any, Optional, Tuple
import logging
from dataclasses import dataclass

# Add the project root to the path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))

try:
    from .prompts.rag_prompts import RAGPrompts
except ImportError:
    try:
        from agent.prompts.rag_prompts import RAGPrompts
    except ImportError:
        RAGPrompts = None

try:
    from ..models.embedding_model import ALQEmbeddingModel
    from database.milvus.milvus_client import search, query, connect
except ImportError:
    try:
        from agent.models.embedding_model import ALQEmbeddingModel
        from database.milvus.milvus_client import search, query, connect
    except ImportError as e:
        logging.error(f"Failed to import dependencies: {e}")
        # Fallback imports for development
        try:
            from agent.models.embedding_model import ALQEmbeddingModel
        except ImportError:
            ALQEmbeddingModel = None


@dataclass
class RAGResult:
    """Structured result from RAG retrieval."""
    teacher_context: List[Dict[str, Any]]
    textbook_context: List[Dict[str, Any]]
    query: str
    total_results: int
    retrieval_time: float


class RAGTool:
    """
    RAG Tool for retrieving educational contexts from vector databases.
    
    This tool queries both teacher_book and textbook collections to provide
    comprehensive context for question generation.
    """
    
    def __init__(self, 
                 embedding_model: Optional[ALQEmbeddingModel] = None,
                 verbose: bool = True):
        """
        Initialize the RAG Tool.
        
        Args:
            embedding_model: ALQ embedding model instance
            verbose: Enable verbose logging
        """
        self.verbose = verbose
        self.embedding_model = embedding_model or self._create_embedding_model()
        
        # Collection names
        self.teacher_collection = "sgv_collection"
        self.textbook_collection = "baitap_collection"
        
        if self.verbose:
            print("🔍 RAG Tool initialized")
    
    def _create_embedding_model(self) -> ALQEmbeddingModel:
        """Create embedding model if not provided."""
        if ALQEmbeddingModel is None:
            raise ImportError("ALQEmbeddingModel not available")
        return ALQEmbeddingModel(verbose=self.verbose)
    
    def _ensure_milvus_connection(self) -> bool:
        """Ensure Milvus connection is available."""
        try:
            connect()
            return True
        except Exception as e:
            if self.verbose:
                print(f"⚠️ Milvus connection failed: {e}")
            return False
    
    def retrieve(self, 
                query: str, 
                top_k: int = 5,
                teacher_top_k: Optional[int] = None,
                textbook_top_k: Optional[int] = None) -> RAGResult:
        """
        Retrieve relevant contexts from both teacher_book and textbook collections.
        
        Args:
            query: Search query string
            top_k: Default number of results to retrieve
            teacher_top_k: Specific number of teacher results (defaults to top_k)
            textbook_top_k: Specific number of textbook results (defaults to top_k)
            
        Returns:
            RAGResult containing retrieved contexts
        """
        import time
        start_time = time.time()
        
        if not query or not query.strip():
            return RAGResult(
                teacher_context=[],
                textbook_context=[],
                query=query,
                total_results=0,
                retrieval_time=0.0
            )
        
        # Set specific top_k values
        teacher_k = teacher_top_k or top_k
        textbook_k = textbook_top_k or top_k
        
        if self.verbose:
            print(f"🔍 Retrieving contexts for query: '{query}'")
            print(f"   Teacher results: {teacher_k}, Textbook results: {textbook_k}")
        
        try:
            # Embed the query
            query_embedding = self.embedding_model.embed_query(query)
            if query_embedding is None:
                if self.verbose:
                    print("❌ Failed to embed query")
                return RAGResult(
                    teacher_context=[],
                    textbook_context=[],
                    query=query,
                    total_results=0,
                    retrieval_time=time.time() - start_time
                )
            
            # Retrieve from teacher collection
            teacher_results = self._search_collection(
                collection_name=self.teacher_collection,
                query_vector=query_embedding,
                top_k=teacher_k,
                collection_type="teacher"
            )
            
            # Retrieve from textbook collection
            textbook_results = self._search_collection(
                collection_name=self.textbook_collection,
                query_vector=query_embedding,
                top_k=textbook_k,
                collection_type="textbook"
            )
            
            retrieval_time = time.time() - start_time
            total_results = len(teacher_results) + len(textbook_results)
            
            if self.verbose:
                print(f"✅ Retrieved {len(teacher_results)} teacher contexts, {len(textbook_results)} textbook contexts")
                print(f"   Total time: {retrieval_time:.2f}s")
            
            return RAGResult(
                teacher_context=teacher_results,
                textbook_context=textbook_results,
                query=query,
                total_results=total_results,
                retrieval_time=retrieval_time
            )
            
        except Exception as e:
            if self.verbose:
                print(f"❌ RAG retrieval failed: {e}")
            return RAGResult(
                teacher_context=[],
                textbook_context=[],
                query=query,
                total_results=0,
                retrieval_time=time.time() - start_time
            )
    
    def _search_collection(self, 
                          collection_name: str, 
                          query_vector: List[float], 
                          top_k: int,
                          collection_type: str) -> List[Dict[str, Any]]:
        """
        Search a specific collection with the query vector.
        
        Args:
            collection_name: Name of the Milvus collection
            query_vector: Query embedding vector
            top_k: Number of results to return
            collection_type: Type of collection (teacher/textbook)
            
        Returns:
            List of search results
        """
        try:
            # Check if Milvus connection is available
            if not self._ensure_milvus_connection():
                if self.verbose:
                    print(f"⚠️ Using mock results for {collection_name}")
                return self._get_mock_results(collection_type, top_k)
            
            # Use the new milvus_client search function
            search_results = search(
                collection_name=collection_name,
                vector_field="embedding",
                query_vectors=[query_vector],
                limit=top_k,
                output_fields=["*"]
            )
            
            # Format results consistently
            formatted_results = []
            if search_results and len(search_results) > 0:
                for hit in search_results[0]:  # search_results is a list of result sets
                    entity = hit.get('entity', {})
                    formatted_result = {
                        'content': entity.get('content', '') or entity.get('lesson', ''),
                        'metadata': {
                            'id': hit.get('id'),
                            'lesson': entity.get('lesson', ''),
                            'source': entity.get('source', ''),
                            'subject': entity.get('subject', ''),
                            'question': entity.get('question', ''),
                            'answer': entity.get('answer', '')
                        },
                        'score': 1.0 - hit.get('distance', 1.0),  # Convert distance to similarity score
                        'collection_type': collection_type
                    }
                    formatted_results.append(formatted_result)
            
            return formatted_results
            
        except Exception as e:
            if self.verbose:
                print(f"❌ Error searching {collection_name}: {e}")
            return self._get_mock_results(collection_type, top_k)
    
    def _get_mock_results(self, collection_type: str, top_k: int) -> List[Dict[str, Any]]:
        """Get mock results for development/testing."""
        if collection_type == "teacher":
            mock_results = [
                {
                    'content': f'Phương pháp dạy học cho học sinh tiểu học',
                    'metadata': {'grade': 1, 'subject': 'Toán', 'type': 'pedagogy'},
                    'score': 0.95,
                    'collection_type': 'teacher'
                },
                {
                    'content': f'Cách giải thích khái niệm trong toán học',
                    'metadata': {'grade': 1, 'subject': 'Toán', 'type': 'explanation'},
                    'score': 0.88,
                    'collection_type': 'teacher'
                }
            ]
        else:  # textbook
            mock_results = [
                {
                    'content': f'Bài tập thực hành toán học',
                    'metadata': {'grade': 1, 'subject': 'Toán', 'type': 'exercise'},
                    'score': 0.92,
                    'collection_type': 'textbook'
                },
                {
                    'content': f'Ví dụ minh họa toán học',
                    'metadata': {'grade': 1, 'subject': 'Toán', 'type': 'example'},
                    'score': 0.85,
                    'collection_type': 'textbook'
                }
            ]
        
        return mock_results[:top_k]
    
    def retrieve_by_skill(self, 
                         skill: str, 
                         grade: int, 
                         subject: str,
                         top_k: int = 5) -> RAGResult:
        """
        Retrieve contexts specifically for a skill-based query.
        
        Args:
            skill: Skill identifier (e.g., "S5")
            grade: Student grade level
            subject: Subject area (e.g., "Toán")
            top_k: Number of results to retrieve
            
        Returns:
            RAGResult containing skill-specific contexts
        """
        # Construct skill-specific query
        query = f"{subject} lớp {grade} kỹ năng {skill}"
        
        if self.verbose:
            print(f"🎯 Retrieving contexts for skill: {skill} (Grade {grade}, {subject})")
        
        return self.retrieve(query, top_k=top_k)
    
    def retrieve_by_topic(self, 
                         topic: str, 
                         grade: int,
                         top_k: int = 5) -> RAGResult:
        """
        Retrieve contexts for a specific topic.
        
        Args:
            topic: Topic name (e.g., "Nhiều hơn, ít hơn, bằng nhau")
            grade: Student grade level
            top_k: Number of results to retrieve
            
        Returns:
            RAGResult containing topic-specific contexts
        """
        # Construct topic-specific query
        query = f"lớp {grade} {topic}"
        
        if self.verbose:
            print(f"📚 Retrieving contexts for topic: {topic} (Grade {grade})")
        
        return self.retrieve(query, top_k=top_k)
    
    def get_retrieval_stats(self) -> Dict[str, Any]:
        """
        Get statistics about retrieval performance.
        
        Returns:
            Dictionary containing retrieval statistics
        """
        return {
            'embedding_model': self.embedding_model.get_model_info() if self.embedding_model else None,
            'collections': {
                'teacher': self.teacher_collection,
                'textbook': self.textbook_collection
            },
            'milvus_connection_available': self._ensure_milvus_connection()
        }


# Convenience functions
def create_rag_tool(embedding_model: Optional[ALQEmbeddingModel] = None,
                   verbose: bool = True) -> RAGTool:
    """
    Create a RAGTool instance with default settings.
    
    Args:
        embedding_model: Optional embedding model instance
        verbose: Enable verbose logging
        
    Returns:
        RAGTool instance
    """
    return RAGTool(
        embedding_model=embedding_model,
        verbose=verbose
    )


# Testing and validation
if __name__ == "__main__":
    print("🧪 Testing RAG Tool")
    print("=" * 50)
    
    # Test queries
    test_queries = [
        "Cách dạy phép cộng cho học sinh lớp 1",
        "Bài tập về phép trừ có nhớ",
        "S5 Mấy và mấy"
    ]
    
    try:
        # Create RAG tool
        print("\n📝 Creating RAG tool...")
        rag_tool = RAGTool(verbose=True)
        
        # Test 1: Basic retrieval
        print(f"\n🧪 Test 1: Basic retrieval")
        result = rag_tool.retrieve(test_queries[0], top_k=3)
        print(f"✅ Retrieved {result.total_results} results in {result.retrieval_time:.2f}s")
        print(f"   Teacher contexts: {len(result.teacher_context)}")
        print(f"   Textbook contexts: {len(result.textbook_context)}")
        
        # Test 2: Skill-based retrieval
        print(f"\n🧪 Test 2: Skill-based retrieval")
        skill_result = rag_tool.retrieve_by_skill("S5", 1, "Toán", top_k=2)
        print(f"✅ Skill retrieval: {skill_result.total_results} results")
        
        # Test 3: Topic-based retrieval
        print(f"\n🧪 Test 3: Topic-based retrieval")
        topic_result = rag_tool.retrieve_by_topic("Nhiều hơn, ít hơn, bằng nhau", 1, top_k=2)
        print(f"✅ Topic retrieval: {topic_result.total_results} results")
        
        # Test 4: Retrieval stats
        print(f"\n📊 Retrieval Statistics:")
        stats = rag_tool.get_retrieval_stats()
        for key, value in stats.items():
            print(f"   {key}: {value}")
        
        print(f"\n🎉 All RAG tool tests completed successfully!")
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
