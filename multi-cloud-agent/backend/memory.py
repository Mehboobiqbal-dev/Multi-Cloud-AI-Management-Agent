import os
import numpy as np
from typing import List, Tuple, Dict, Any
# from annoy import AnnoyIndex
import google.generativeai as genai
import json
from core.config import settings

# Configure the generative AI model with the API key from settings
if settings.GEMINI_API_KEY:
    genai.configure(api_key=settings.GEMINI_API_KEY)
else:
    print("Warning: GEMINI_API_KEY not set. Memory features will be limited.")
    # We'll continue without raising an exception to allow the app to start

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

    def _get_embedding(self, text: str) -> np.ndarray:
        """
        Generates an embedding for the given text using Google's service.
        """
        try:
            result = genai.embed_content(
                model=self.embedding_model,
                content=text,
                task_type="retrieval_document"
            )
            return np.array(result['embedding'], dtype=np.float32)
        except Exception as e:
            print(f"Warning: Failed to generate embedding: {e}")
            # Return zero vector as fallback
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
