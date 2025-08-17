import os
import numpy as np
from typing import List, Tuple, Dict, Any, Optional
# from annoy import AnnoyIndex
import google.generativeai as genai
import json
import time
from datetime import datetime
from core.config import settings
import logging
from core.circuit_breaker import get_circuit_breaker, CircuitBreakerConfig, CircuitBreakerOpenError
from core.local_embeddings import local_embedding_fallback, LocalEmbeddingError
from core.structured_logging import structured_logger, LogContext, operation_context

# No global configuration - embeddings will be generated with key rotation
# Key configuration is handled per request in _generate_external_embedding method

class Memory:
    def __init__(self, embedding_dim: int = 768):
        """
        Initializes the Memory class.
        Args:
            embedding_dim: The dimension of the embeddings. Google's model uses 768.
        """
        self.embedding_dim = embedding_dim
        # self.index = AnnoyIndex(embedding_dim, 'angular')
        self.documents: List[str] = []
        self.embeddings: List[np.ndarray] = []  # Store embeddings for cosine similarity
        self.item_counter = 0
        # The model for embedding
        self.embedding_model = 'models/embedding-001'
        # Circuit breaker state
        self._embed_failures = 0
        self._embed_open_until = 0.0

    def _get_embedding(self, text: str) -> np.ndarray:
        """
        Generates an embedding for the given text using Google's service.
        Implements circuit breaker and local fallback for enhanced resilience.
        """
        if not text.strip():
            return np.zeros(self.embedding_dim, dtype=np.float32)
        
        # Truncate text if it exceeds Gemini's 36KB limit (approximately 30,000 characters)
        max_chars = 30000
        if len(text) > max_chars:
            text = text[:max_chars]
            logging.warning(f"Text truncated from {len(text)} to {max_chars} characters for embedding generation")
        
        # Get circuit breaker for embeddings
        circuit_breaker = get_circuit_breaker(
            'embedding_generation',
            CircuitBreakerConfig(
                failure_threshold=getattr(settings, 'CIRCUIT_BREAKER_FAILURE_THRESHOLD', 5),
                recovery_timeout=float(getattr(settings, 'CIRCUIT_BREAKER_RECOVERY_TIMEOUT', 60.0)),
                expected_exception=Exception,
                name='embedding_generation'
            )
        )
        
        context = LogContext(metadata={'text_length': len(text)})
        
        try:
            with operation_context('generate_embedding', context):
                # Try to use circuit breaker protected external embedding
                embedding_list = circuit_breaker.call(self._generate_external_embedding, text)
                return np.array(embedding_list, dtype=np.float32)
                
        except CircuitBreakerOpenError:
            # Circuit is open, try local fallback
            structured_logger.log_circuit_breaker_event('embedding_generation', 'open', context)
            return self._generate_fallback_embedding(text, context)
        
        except Exception as e:
            # External embedding failed, try local fallback
            structured_logger.log_retry_attempt('embedding_generation', 0, str(e), context)
            return self._generate_fallback_embedding(text, context)

    def _generate_external_embedding(self, text: str) -> List[float]:
        """Generate embedding using external service (Gemini) with API key failover."""
        # Build the list of API keys to try
        api_keys = []
        
        if settings.GEMINI_API_KEYS_LIST:
            api_keys.extend(settings.GEMINI_API_KEYS_LIST)
            logging.info(f"Added {len(settings.GEMINI_API_KEYS_LIST)} keys from GEMINI_API_KEYS_LIST for embeddings")
        
        if settings.GEMINI_API_KEY and settings.GEMINI_API_KEY not in api_keys:
            api_keys.append(settings.GEMINI_API_KEY)
            logging.info(f"Added single GEMINI_API_KEY as backup for embeddings")
        
        if not api_keys:
            raise Exception("No Gemini API keys configured for embeddings.")

        logging.info(f"Starting Gemini embedding generation with {len(api_keys)} available API keys")
        
        last_exception = None
        quota_exhausted_count = 0
        keys_attempted = 0
        max_retries = getattr(settings, "MAX_RETRIES", 3)
        retry_delay = float(getattr(settings, "INITIAL_RETRY_DELAY", 2.0))

        for i, key in enumerate(api_keys):
            keys_attempted += 1
            key_prefix = key[:10] if len(key) >= 10 else key[:6]
            
            for attempt in range(max_retries):
                try:
                    logging.info(f"Attempting Gemini embedding with key #{i+1} ({key_prefix}...), attempt {attempt+1}")
                    
                    genai.configure(api_key=key)
                    result = genai.embed_content(
                        model=self.embedding_model,
                        content=text,
                        task_type="retrieval_document"
                    )
                    logging.info(f"✅ Successfully generated embedding using key #{i+1} ({key_prefix}...)")
                    return result['embedding']
                    
                except Exception as e:
                    error_msg = str(e).lower()
                    
                    # Check for quota/rate limit errors
                    if "quota" in error_msg or "429" in error_msg or "resource_exhausted" in error_msg:
                        quota_exhausted_count += 1
                        logging.warning(f"❌ Gemini embedding quota exceeded for key #{i+1} ({key_prefix}...): {e}")
                        last_exception = e
                        break  # Move to next key
                    
                    # Check for non-retriable errors (argument errors)
                    if any(msg in error_msg for msg in ["invalid argument", "bad request", "400", "unexpected keyword argument"]):
                        logging.error(f"❌ Non-retriable error with key #{i+1} ({key_prefix}...): {e}")
                        last_exception = e
                        break  # Move to next key
                    
                    # Check for connection-related errors
                    is_connection_error = any(msg in error_msg for msg in [
                        "failed to connect", "timeout", "connection refused", 
                        "network", "socket", "unreachable", "tcp handshaker shutdown", "dns", "gateway"
                    ])
                    
                    if is_connection_error and attempt < max_retries - 1:
                        structured_logger.log_retry_attempt('external_embedding', attempt + 1, str(e))
                        time.sleep(retry_delay)
                        retry_delay = min(retry_delay * 2, float(getattr(settings, "MAX_RETRY_DELAY", 60.0)))
                        continue  # Retry with same key
                    
                    # Other errors or final attempt failed
                    logging.warning(f"❌ Gemini embedding error with key #{i+1} ({key_prefix}...): {e}")
                    last_exception = e
                    break  # Move to next key

        # If we reach here, all keys failed
        logging.error(f"All {keys_attempted} Gemini embedding API keys failed. Quota exhausted: {quota_exhausted_count}, Other errors: {keys_attempted - quota_exhausted_count}")
        
        if quota_exhausted_count == keys_attempted and quota_exhausted_count > 0:
            raise Exception(f"All {keys_attempted} Gemini embedding API keys have exceeded quota. Please try again later.")
        
        raise Exception(f"Gemini embedding generation failed for all {keys_attempted} keys: {last_exception}")

    def _generate_fallback_embedding(self, text: str, context: Optional[LogContext] = None) -> np.ndarray:
        """Generate embedding using local fallback."""
        try:
            structured_logger.log_self_learning_event(
                "Using local embedding fallback",
                context,
                {'fallback_reason': 'external_service_unavailable'}
            )
            
            if local_embedding_fallback.available:
                embedding_list = local_embedding_fallback.embed_text(text)
                return np.array(embedding_list, dtype=np.float32)
            else:
                # Local fallback not available, return zero vector
                structured_logger.log_self_learning_event(
                    "Local embedding fallback not available, using zero vector",
                    context
                )
                return np.zeros(self.embedding_dim, dtype=np.float32)
                
        except LocalEmbeddingError as e:
            structured_logger.log_self_learning_event(
                f"Local embedding fallback failed: {e}",
                context
            )
            # Return zero vector as last resort
            return np.zeros(self.embedding_dim, dtype=np.float32)

    def _cosine_similarity(self, a: np.ndarray, b: np.ndarray) -> float:
        """Compute cosine similarity between two vectors using numpy."""
        a_norm = np.linalg.norm(a) + 1e-8
        b_norm = np.linalg.norm(b) + 1e-8
        return float(np.dot(a, b) / (a_norm * b_norm))

    def add_document(self, data: Dict[str, Any]):
        """
        Adds a structured document to the memory. The embedding is computed and stored.
        """
        text_representation = json.dumps(data)
        embedding = self._get_embedding(text_representation)
        
        # Store both document and embedding
        self.documents.append(text_representation)
        self.embeddings.append(embedding)
        self.item_counter += 1

    def search(self, query: str, k: int = 5) -> List[Tuple[float, Dict[str, Any]]]:
        """
        Searches the memory for similar documents using cosine similarity.
        """
        if not self.documents:
            return []

        try:
            # Get query embedding
            query_embedding = self._get_embedding(query)
            
            # Compute cosine similarities with all stored embeddings
            similarities = []
            for i, doc_embedding in enumerate(self.embeddings):
                similarity = self._cosine_similarity(query_embedding, doc_embedding)
                similarities.append((similarity, i))
            
            # Sort by similarity (descending) and get top k
            similarities.sort(key=lambda x: x[0], reverse=True)
            
            results = []
            for similarity, doc_index in similarities[:k]:
                try:
                    # Convert similarity to distance (lower is better)
                    distance = 1.0 - similarity
                    doc_data = json.loads(self.documents[doc_index])
                    results.append((distance, doc_data))
                except json.JSONDecodeError:
                    continue  # Skip malformed entries
            
            return results
            
        except Exception as e:
            print(f"Warning: Cosine similarity search failed: {e}")
            # Fall back to recent documents
            num_docs_to_return = min(k, len(self.documents))
            
            results = []
            for doc_str in reversed(self.documents[-num_docs_to_return:]):
                try:
                    # The "distance" is a placeholder value.
                    results.append((0.0, json.loads(doc_str)))
                except json.JSONDecodeError:
                    continue  # Skip malformed entries
            
            return results

# Global instance of the Memory class
memory_instance = Memory()

def get_memory_instance() -> Memory:
    """Returns the global memory instance for compatibility with main.py"""
    return memory_instance
