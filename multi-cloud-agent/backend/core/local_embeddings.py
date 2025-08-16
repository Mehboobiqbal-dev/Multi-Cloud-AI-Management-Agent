"""Local embedding fallback for resilience.

Provides local embedding generation using sentence-transformers
when external embedding services are unavailable.
"""

import os
import numpy as np
from typing import List, Optional, Union
import threading
from functools import lru_cache
from core.config import settings
from core.logging import get_logger
from core.structured_logging import structured_logger, LogContext, operation_context

logger = get_logger(__name__)

# Global variables for lazy loading
_model = None
_model_lock = threading.Lock()
_model_loaded = False
_load_error = None


class LocalEmbeddingError(Exception):
    """Exception raised when local embedding generation fails."""
    pass


def _load_model():
    """Lazy load the sentence transformer model."""
    global _model, _model_loaded, _load_error
    
    if _model_loaded:
        if _load_error:
            raise LocalEmbeddingError(f"Model loading failed previously: {_load_error}")
        return _model
    
    with _model_lock:
        if _model_loaded:
            if _load_error:
                raise LocalEmbeddingError(f"Model loading failed previously: {_load_error}")
            return _model
        
        try:
            with operation_context('load_local_embedding_model'):
                # Respect configuration flag to disable local embeddings
                if not getattr(settings, 'ENABLE_LOCAL_EMBEDDINGS', False):
                    _load_error = "Local embeddings disabled by configuration"
                    _model_loaded = True
                    raise LocalEmbeddingError(_load_error)
                
                # Try to import sentence-transformers
                try:
                    from sentence_transformers import SentenceTransformer
                except ImportError as e:
                    _load_error = f"sentence-transformers not installed: {e}"
                    _model_loaded = True
                    raise LocalEmbeddingError(_load_error)
                
                # Get model name from settings
                model_name = getattr(settings, 'LOCAL_EMBEDDING_MODEL', 'sentence-transformers/all-MiniLM-L6-v2')
                
                logger.info(f"Loading local embedding model: {model_name}")
                
                # Load the model
                _model = SentenceTransformer(model_name)
                _model_loaded = True
                
                logger.info(f"Successfully loaded local embedding model: {model_name}")
                structured_logger.log_self_learning_event(
                    f"Local embedding model loaded: {model_name}",
                    extra_data={'model_name': model_name}
                )
                
                return _model
                
        except Exception as e:
            _load_error = str(e)
            _model_loaded = True
            logger.error(f"Failed to load local embedding model: {e}")
            raise LocalEmbeddingError(f"Failed to load model: {e}")


def is_available() -> bool:
    """Check if local embeddings are available."""
    try:
        _load_model()
        return True
    except LocalEmbeddingError:
        return False


def generate_embedding(text: str, normalize: bool = True) -> List[float]:
    """Generate embedding for a single text.
    
    Args:
        text: Input text to embed
        normalize: Whether to normalize the embedding vector
    
    Returns:
        List of floats representing the embedding
    
    Raises:
        LocalEmbeddingError: If embedding generation fails
    """
    if not text or not text.strip():
        # Return zero vector for empty text
        embedding_dim = getattr(settings, 'LOCAL_EMBEDDING_DIMENSION', 384)
        return [0.0] * embedding_dim
    
    try:
        with operation_context('generate_local_embedding', LogContext(metadata={'text_length': len(text)})):
            model = _load_model()
            
            # Generate embedding
            embedding = model.encode([text.strip()], normalize_embeddings=normalize)[0]
            
            # Convert to list
            if isinstance(embedding, np.ndarray):
                embedding = embedding.tolist()
            
            logger.debug(f"Generated local embedding for text of length {len(text)}")
            return embedding
            
    except Exception as e:
        logger.error(f"Failed to generate local embedding: {e}")
        raise LocalEmbeddingError(f"Embedding generation failed: {e}")


def generate_embeddings_batch(texts: List[str], normalize: bool = True, batch_size: Optional[int] = None) -> List[List[float]]:
    """Generate embeddings for multiple texts in batch.
    
    Args:
        texts: List of input texts to embed
        normalize: Whether to normalize the embedding vectors
        batch_size: Batch size for processing (uses settings default if None)
    
    Returns:
        List of embedding vectors
    
    Raises:
        LocalEmbeddingError: If embedding generation fails
    """
    if not texts:
        return []
    
    if batch_size is None:
        batch_size = getattr(settings, 'LOCAL_EMBEDDING_BATCH_SIZE', 32)
    
    try:
        with operation_context('generate_local_embeddings_batch', 
                              LogContext(metadata={'num_texts': len(texts), 'batch_size': batch_size})):
            model = _load_model()
            
            # Process texts in batches
            all_embeddings = []
            embedding_dim = getattr(settings, 'LOCAL_EMBEDDING_DIMENSION', 384)
            
            for i in range(0, len(texts), batch_size):
                batch_texts = texts[i:i + batch_size]
                
                # Clean and prepare texts
                cleaned_texts = []
                for text in batch_texts:
                    if text and text.strip():
                        cleaned_texts.append(text.strip())
                    else:
                        cleaned_texts.append("")  # Empty string for empty inputs
                
                # Generate embeddings for batch
                if any(cleaned_texts):  # Only process if there are non-empty texts
                    batch_embeddings = model.encode(cleaned_texts, normalize_embeddings=normalize)
                    
                    # Convert to list format
                    for j, embedding in enumerate(batch_embeddings):
                        if cleaned_texts[j]:  # Non-empty text
                            if isinstance(embedding, np.ndarray):
                                embedding = embedding.tolist()
                            all_embeddings.append(embedding)
                        else:  # Empty text
                            all_embeddings.append([0.0] * embedding_dim)
                else:
                    # All texts in batch are empty
                    for _ in batch_texts:
                        all_embeddings.append([0.0] * embedding_dim)
            
            logger.info(f"Generated {len(all_embeddings)} local embeddings in batches of {batch_size}")
            return all_embeddings
            
    except Exception as e:
        logger.error(f"Failed to generate local embeddings batch: {e}")
        raise LocalEmbeddingError(f"Batch embedding generation failed: {e}")


@lru_cache(maxsize=getattr(settings, 'LOCAL_EMBEDDING_CACHE_SIZE', 1000))
def generate_embedding_cached(text: str, normalize: bool = True) -> tuple:
    """Generate embedding with caching.
    
    Args:
        text: Input text to embed
        normalize: Whether to normalize the embedding vector
    
    Returns:
        Tuple of floats representing the embedding (for hashability)
    
    Raises:
        LocalEmbeddingError: If embedding generation fails
    """
    embedding = generate_embedding(text, normalize)
    return tuple(embedding)


def get_embedding_dimension() -> int:
    """Get the dimension of embeddings from the loaded model.
    
    Returns:
        Embedding dimension
    
    Raises:
        LocalEmbeddingError: If model is not available
    """
    try:
        model = _load_model()
        # Get dimension from model
        if hasattr(model, 'get_sentence_embedding_dimension'):
            return model.get_sentence_embedding_dimension()
        elif hasattr(model, 'encode'):
            # Test with a sample text to get dimension
            test_embedding = model.encode(["test"], normalize_embeddings=False)[0]
            return len(test_embedding)
        else:
            # Fallback to settings
            return getattr(settings, 'LOCAL_EMBEDDING_DIMENSION', 384)
    except Exception as e:
        logger.warning(f"Could not determine embedding dimension: {e}")
        return getattr(settings, 'LOCAL_EMBEDDING_DIMENSION', 384)


def clear_cache():
    """Clear the embedding cache."""
    generate_embedding_cached.cache_clear()
    logger.info("Local embedding cache cleared")


def get_cache_info():
    """Get cache statistics."""
    return generate_embedding_cached.cache_info()


def reset_model():
    """Reset the loaded model (for testing or reloading)."""
    global _model, _model_loaded, _load_error
    
    with _model_lock:
        _model = None
        _model_loaded = False
        _load_error = None
        clear_cache()
        logger.info("Local embedding model reset")


class LocalEmbeddingFallback:
    """Fallback embedding provider using local models."""
    
    def __init__(self):
        self.available = None
        self._check_availability()
    
    def _check_availability(self):
        """Check if local embeddings are available."""
        try:
            # If disabled by configuration, mark unavailable without attempting to load
            if not getattr(settings, 'ENABLE_LOCAL_EMBEDDINGS', False):
                logger.info("Local embedding fallback disabled by configuration")
                self.available = False
                return
            
            self.available = is_available()
            if self.available:
                logger.info("Local embedding fallback is available")
            else:
                logger.warning("Local embedding fallback is not available")
        except Exception as e:
            logger.error(f"Error checking local embedding availability: {e}")
            self.available = False
    
    def embed_text(self, text: str, use_cache: bool = True) -> List[float]:
        """Embed a single text with optional caching.
        
        Args:
            text: Text to embed
            use_cache: Whether to use caching
        
        Returns:
            Embedding vector
        
        Raises:
            LocalEmbeddingError: If embedding fails
        """
        if not self.available:
            raise LocalEmbeddingError("Local embeddings not available")
        
        if use_cache:
            return list(generate_embedding_cached(text))
        else:
            return generate_embedding(text)
    
    def embed_texts(self, texts: List[str], batch_size: Optional[int] = None) -> List[List[float]]:
        """Embed multiple texts.
        
        Args:
            texts: List of texts to embed
            batch_size: Batch size for processing
        
        Returns:
            List of embedding vectors
        
        Raises:
            LocalEmbeddingError: If embedding fails
        """
        if not self.available:
            raise LocalEmbeddingError("Local embeddings not available")
        
        return generate_embeddings_batch(texts, batch_size=batch_size)
    
    def get_dimension(self) -> int:
        """Get embedding dimension.
        
        Returns:
            Embedding dimension
        """
        if not self.available:
            return getattr(settings, 'LOCAL_EMBEDDING_DIMENSION', 384)
        
        return get_embedding_dimension()


# Global fallback instance
local_embedding_fallback = LocalEmbeddingFallback()