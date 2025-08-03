import os
import numpy as np
from typing import List, Tuple, Dict, Any
# from annoy import AnnoyIndex
import google.generativeai as genai
import json

# Configure the generative AI model with the API key from environment variables
try:
    genai.configure(api_key=os.environ["GEMINI_API_KEY"])
except KeyError:
    raise ValueError("GEMINI_API_KEY environment variable not set.")

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
        self.item_counter = 0
        self.index_built = False
        # The model for embedding
        self.embedding_model = 'models/embedding-001'

    def _get_embedding(self, text: str) -> np.ndarray:
        """
        Generates an embedding for the given text using Google's service.
        """
        result = genai.embed_content(
            model=self.embedding_model,
            content=text,
            task_type="retrieval_document"
        )
        return np.array(result['embedding'], dtype=np.float32)

    def add_document(self, data: Dict[str, Any]):
        """
        Adds a structured document to the memory. The index will need to be rebuilt.
        """
        text_representation = json.dumps(data)
        embedding = self._get_embedding(text_representation)
        # self.index.add_item(self.item_counter, embedding)
        self.documents.append(text_representation)
        self.item_counter += 1
        self.index_built = False  # Mark index as not built

    def search(self, query: str, k: int = 5) -> List[Tuple[float, Dict[str, Any]]]:
        """
        Searches the memory for similar documents.
        """
        if not self.documents:
            return []

        if not self.index_built:
            # Build the index if it hasn't been built yet. 10 trees is a good balance.
            # self.index.build(10)
            self.index_built = True

        query_embedding = self._get_embedding(query)
        # For now, as Annoy is disabled, we'll return the most recent interactions.
        # This is a placeholder for a real vector search.
        num_docs_to_return = min(k, len(self.documents))
        
        results = []
        for doc_str in reversed(self.documents[-num_docs_to_return:]):
            try:
                # The "distance" is a placeholder value.
                results.append((0.0, json.loads(doc_str)))
            except json.JSONDecodeError:
                continue # Skip malformed entries
        
        return results

# Global instance of the Memory class
memory_instance = Memory()
