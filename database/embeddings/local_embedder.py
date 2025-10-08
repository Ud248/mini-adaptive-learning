"""
Vietnamese Text Embedding Service
=================================

Optimized local embedding service for Vietnamese text using sentence-transformers.
Designed to be called from other modules before inserting into vector databases.
"""

import numpy as np
import torch
from sentence_transformers import SentenceTransformer
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading
import time
from typing import List, Optional, Union, Dict, Any

# Default configuration
DEFAULT_MODEL = 'dangvantuan/vietnamese-document-embedding'
DEFAULT_BATCH_SIZE = 16
DEFAULT_MAX_WORKERS = 2
EMBEDDING_DIMENSION = 768


class LocalEmbedding:
    """
    Vietnamese text embedding service optimized for vector database insertion
    
    Features:
    - GPU/CPU automatic detection
    - Memory management for large datasets
    - Batch processing with parallel workers
    - Error handling and retry logic
    - Progress tracking
    """
    
    def __init__(self, model_name: str = DEFAULT_MODEL, batch_size: int = DEFAULT_BATCH_SIZE, verbose: bool = True):
        """
        Initialize Vietnamese embedding model
        
        Args:
            model_name: HuggingFace model name
            batch_size: Batch size for processing
            verbose: Print initialization info
        """
        self.model_name = model_name
        self.batch_size = batch_size
        self.verbose = verbose
        self.device = 'cuda' if torch.cuda.is_available() else 'cpu'
        self._lock = threading.Lock()
        self._model = None
        
        if self.verbose:
            print(f"🔧 Initializing Vietnamese Embedding Service")
            print(f"   Model: {model_name}")
            print(f"   Device: {self.device}")
            print(f"   Batch size: {batch_size}")
        
        self._load_model()
    
    def _load_model(self) -> None:
        """Load the sentence transformer model with error handling"""
        try:
            start_time = time.time()
            self._model = SentenceTransformer(
                self.model_name, 
                device=self.device, 
                trust_remote_code=True
            )
            
            load_time = time.time() - start_time
            
            if self.verbose:
                print(f"✅ Model loaded in {load_time:.2f}s")
                
                if self.device.startswith('cuda'):
                    gpu_memory = torch.cuda.get_device_properties(0).total_memory / 1024**3
                    print(f"🔥 GPU Memory: {gpu_memory:.1f}GB")
                    
        except Exception as e:
            print(f"❌ Error loading model: {e}")
            raise RuntimeError(f"Failed to load embedding model: {e}")
    
    @property
    def model(self):
        """Lazy loading of model"""
        if self._model is None:
            self._load_model()
        return self._model
    
    def embed_texts(self, texts: List[str]) -> List[List[float]]:
        """
        Core embedding function - embed list of texts into vectors
        
        Args:
            texts: List of text strings to embed
            
        Returns:
            List of embedding vectors (each vector is List[float])
            
        Raises:
            ValueError: If embedding fails after retries
        """
        if not texts:
            return []
        
        # Filter empty texts
        valid_texts = []
        original_indices = []
        
        for i, text in enumerate(texts):
            if text and text.strip():
                valid_texts.append(text.strip())
                original_indices.append(i)
        
        if not valid_texts:
            return [[0.0] * EMBEDDING_DIMENSION] * len(texts)
        
        try:
            with self._lock:
                embeddings = self._generate_embeddings(valid_texts)
                
                # Map back to original positions
                result = [[0.0] * EMBEDDING_DIMENSION] * len(texts)
                for i, embedding in enumerate(embeddings):
                    original_index = original_indices[i]
                    result[original_index] = embedding
                
                return result
                
        except Exception as e:
            if self.verbose:
                print(f"❌ Embedding failed: {e}")
            raise ValueError(f"Failed to generate embeddings: {e}")
    
    def _generate_embeddings(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings with memory management and retry logic"""
        try:
            # Clear CUDA cache
            if self.device.startswith('cuda'):
                torch.cuda.empty_cache()
            
            # Generate embeddings
            embeddings = self.model.encode(
                texts,
                convert_to_tensor=False,
                normalize_embeddings=True,
                batch_size=self.batch_size,
                show_progress_bar=False,
                device=self.device
            )
            
            # Convert to list format
            result = []
            for embedding in embeddings:
                if isinstance(embedding, np.ndarray):
                    result.append(embedding.tolist())
                else:
                    result.append(list(embedding))
            
            # Clear cache after processing
            if self.device.startswith('cuda'):
                torch.cuda.empty_cache()
            
            return result
            
        except torch.cuda.OutOfMemoryError:
            if self.verbose:
                print(f"🔥 CUDA OOM - retrying with smaller batch")
            return self._retry_with_smaller_batch(texts)
        
        except Exception as e:
            if self.device.startswith('cuda'):
                torch.cuda.empty_cache()
            raise e
    
    def _retry_with_smaller_batch(self, texts: List[str]) -> List[List[float]]:
        """Retry embedding with reduced batch size on OOM"""
        try:
            torch.cuda.empty_cache()
            
            # Use smaller batch size
            smaller_batch = max(1, self.batch_size // 2)
            
            embeddings = self.model.encode(
                texts,
                convert_to_tensor=False,
                normalize_embeddings=True,
                batch_size=smaller_batch,
                show_progress_bar=False,
                device=self.device
            )
            
            result = []
            for embedding in embeddings:
                if isinstance(embedding, np.ndarray):
                    result.append(embedding.tolist())
                else:
                    result.append(list(embedding))
            
            torch.cuda.empty_cache()
            return result
            
        except Exception as e:
            torch.cuda.empty_cache()
            raise ValueError(f"Failed to generate embeddings even with reduced batch size: {e}")
    
    def embed_texts_parallel(
        self, 
        texts: List[str], 
        max_workers: int = DEFAULT_MAX_WORKERS, 
        show_progress: bool = True
    ) -> List[List[float]]:
        """
        Embed large list of texts using parallel processing
        
        Args:
            texts: List of texts to embed
            max_workers: Number of parallel workers
            show_progress: Show progress information
            
        Returns:
            List of embedding vectors
        """
        if not texts:
            return []
        
        if len(texts) <= self.batch_size:
            # Small dataset, use regular embedding
            return self.embed_texts(texts)
        
        if show_progress:
            print(f"🚀 Embedding {len(texts)} texts in parallel...")
            print(f"   Workers: {max_workers}")
            print(f"   Batch size: {self.batch_size}")
        
        # Split into chunks for parallel processing
        chunk_size = max(self.batch_size, len(texts) // max_workers)
        text_chunks = [texts[i:i + chunk_size] for i in range(0, len(texts), chunk_size)]
        
        all_embeddings = []
        successful_batches = 0
        
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            # Submit embedding tasks
            future_to_chunk = {
                executor.submit(self.embed_texts, chunk): i 
                for i, chunk in enumerate(text_chunks)
            }
            
            # Collect results in order
            chunk_results = [None] * len(text_chunks)
            
            for future in as_completed(future_to_chunk):
                chunk_idx = future_to_chunk[future]
                try:
                    embeddings = future.result()
                    chunk_results[chunk_idx] = embeddings
                    successful_batches += 1
                    
                    if show_progress:
                        print(f"✅ Chunk {chunk_idx + 1}/{len(text_chunks)} completed")
                        
                except Exception as e:
                    if show_progress:
                        print(f"❌ Chunk {chunk_idx + 1} failed: {e}")
                    
                    # Create zero embeddings for failed chunk
                    chunk_size = len(text_chunks[chunk_idx])
                    chunk_results[chunk_idx] = [[0.0] * EMBEDDING_DIMENSION] * chunk_size
            
            # Flatten results
            for chunk_embeddings in chunk_results:
                if chunk_embeddings:
                    all_embeddings.extend(chunk_embeddings)
        
        if show_progress:
            print(f"📊 Embedding completed: {len(all_embeddings)} vectors")
            print(f"   Success rate: {successful_batches}/{len(text_chunks)} chunks")
        
        return all_embeddings
    
    def embed_single_text(self, text: str) -> Optional[List[float]]:
        """
        Embed single text string
        
        Args:
            text: Text to embed
            
        Returns:
            Embedding vector or None if text is empty
        """
        if not text or not text.strip():
            return None
        
        result = self.embed_texts([text])
        return result[0] if result else None
    
    def get_embedding_dimension(self) -> int:
        """Get the dimension of embeddings produced by this model"""
        return EMBEDDING_DIMENSION
    
    def embed_chunks_for_database(self, chunks: List[Dict[str, Any]], text_field: str = 'content') -> List[Dict[str, Any]]:
        """
        Specialized method for embedding chunks before database insertion
        
        Args:
            chunks: List of chunk dictionaries
            text_field: Field name containing text to embed
            
        Returns:
            List of chunks with added 'embedding' field
        """
        if not chunks:
            return []
        
        if self.verbose:
            print(f"🔥 Embedding {len(chunks)} chunks for database insertion...")
        
        # Extract texts
        texts = []
        valid_chunks = []
        
        for chunk in chunks:
            text = chunk.get(text_field, '')
            if text and text.strip():
                texts.append(text.strip())
                valid_chunks.append(chunk)
        
        if not texts:
            if self.verbose:
                print("⚠️ No valid texts found in chunks")
            return chunks
        
        # Generate embeddings
        try:
            if len(texts) > 50:  # Use parallel for large datasets
                embeddings = self.embed_texts_parallel(texts, show_progress=self.verbose)
            else:
                embeddings = self.embed_texts(texts)
            
            # Add embeddings to chunks
            result_chunks = []
            embedding_idx = 0
            
            for chunk in chunks:
                chunk_copy = chunk.copy()
                text = chunk.get(text_field, '')
                
                if text and text.strip():
                    if embedding_idx < len(embeddings):
                        chunk_copy['embedding'] = embeddings[embedding_idx]
                        embedding_idx += 1
                    else:
                        chunk_copy['embedding'] = [0.0] * EMBEDDING_DIMENSION
                else:
                    chunk_copy['embedding'] = [0.0] * EMBEDDING_DIMENSION
                
                result_chunks.append(chunk_copy)
            
            if self.verbose:
                successful_embeddings = sum(1 for chunk in result_chunks if chunk.get('embedding') != [0.0] * EMBEDDING_DIMENSION)
                print(f"✅ Successfully embedded {successful_embeddings}/{len(chunks)} chunks")
            
            return result_chunks
            
        except Exception as e:
            if self.verbose:
                print(f"❌ Failed to embed chunks: {e}")
            
            # Return chunks with zero embeddings as fallback
            for chunk in chunks:
                chunk['embedding'] = [0.0] * EMBEDDING_DIMENSION
            
            return chunks
    
    def cleanup(self) -> None:
        """Clean up GPU memory and resources"""
        if self.device.startswith('cuda'):
            torch.cuda.empty_cache()
        
        if self.verbose:
            print("🧹 Cleaned up GPU memory")
    
    def get_model_info(self) -> Dict[str, Any]:
        """Get information about the loaded model"""
        return {
            'model_name': self.model_name,
            'device': self.device,
            'batch_size': self.batch_size,
            'embedding_dimension': EMBEDDING_DIMENSION,
            'cuda_available': torch.cuda.is_available()
        }


# Convenience functions for quick usage
def create_embedder(model_name: str = DEFAULT_MODEL, batch_size: int = DEFAULT_BATCH_SIZE, verbose: bool = True) -> LocalEmbedding:
    """Create a LocalEmbedding instance with default settings"""
    return LocalEmbedding(model_name=model_name, batch_size=batch_size, verbose=verbose)


def embed_text_quick(text: str, embedder: Optional[LocalEmbedding] = None) -> Optional[List[float]]:
    """Quick function to embed single text"""
    if embedder is None:
        embedder = create_embedder(verbose=False)
    
    try:
        return embedder.embed_single_text(text)
    finally:
        embedder.cleanup()


def embed_texts_quick(texts: List[str], embedder: Optional[LocalEmbedding] = None) -> List[List[float]]:
    """Quick function to embed multiple texts"""
    if embedder is None:
        embedder = create_embedder(verbose=False)
    
    try:
        return embedder.embed_texts(texts)
    finally:
        embedder.cleanup()


# Legacy compatibility
VietnameseEmbedder = LocalEmbedding


# Testing and validation
if __name__ == "__main__":
    print("🧪 Testing Vietnamese Embedding Service")
    print("=" * 50)
    
    # Test texts
    test_texts = [
        "Xin chào, tôi là trí tuệ nhân tạo.",
        "Hôm nay là một ngày đẹp trời.",
        "Machine learning rất thú vị.",
        "Chúng ta đang phát triển hệ thống RAG tiếng Việt.",
        "Vector database sẽ lưu trữ embeddings."
    ]
    
    # Test chunks (simulating database chunks)
    test_chunks = [
        {
            'chunk_id': 'chunk_1',
            'title': 'Chương 1: Giới thiệu',
            'content': 'Đây là nội dung chương giới thiệu về AI.',
            'level': 1
        },
        {
            'chunk_id': 'chunk_2', 
            'title': 'Chương 2: Machine Learning',
            'content': 'Machine learning là một phần quan trọng của AI.',
            'level': 1
        }
    ]
    
    try:
        # Create embedder
        print("\n📝 Creating embedder...")
        embedder = LocalEmbedding()
        
        # Test 1: Single text embedding
        print(f"\n🧪 Test 1: Single text embedding")
        single_embedding = embedder.embed_single_text(test_texts[0])
        if single_embedding:
            print(f"✅ Single embedding dimension: {len(single_embedding)}")
        else:
            print("❌ Single embedding failed")
        
        # Test 2: Batch embedding
        print(f"\n🧪 Test 2: Batch embedding")
        batch_embeddings = embedder.embed_texts(test_texts)
        print(f"✅ Batch embeddings: {len(batch_embeddings)} vectors")
        
        # Test 3: Parallel embedding
        print(f"\n🧪 Test 3: Parallel embedding")
        large_texts = test_texts * 10  # 50 texts
        parallel_embeddings = embedder.embed_texts_parallel(large_texts, max_workers=2)
        print(f"✅ Parallel embeddings: {len(parallel_embeddings)} vectors")
        
        # Test 4: Database chunks embedding
        print(f"\n🧪 Test 4: Database chunks embedding")
        embedded_chunks = embedder.embed_chunks_for_database(test_chunks)
        print(f"✅ Embedded chunks: {len(embedded_chunks)}")
        for chunk in embedded_chunks:
            print(f"   {chunk['chunk_id']}: embedding dim = {len(chunk['embedding'])}")
        
        # Test 5: Model info
        print(f"\n📊 Model Information:")
        model_info = embedder.get_model_info()
        for key, value in model_info.items():
            print(f"   {key}: {value}")
        
        # Cleanup
        embedder.cleanup()
        print(f"\n🎉 All tests completed successfully!")
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()