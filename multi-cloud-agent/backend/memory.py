import faiss
import numpy as np
from typing import List, Tuple
from sentence_transformers import SentenceTransformer

class Memory:
    def __init__(self, embedding_dim: int = 768):
        self.embedding_dim = embedding_dim
        self.index = faiss.IndexFlatL2(embedding_dim)
        self.documents: List[str] = []
        self.model = SentenceTransformer('all-MiniLM-L6-v2')

    def add_document(self, text: str):
        """
        Adds a document to the memory.
        """
        embedding = self.model.encode([text])
        self.index.add(np.array(embedding, dtype=np.float32))
        self.documents.append(text)

    def search(self, query: str, k: int = 5) -> List[Tuple[float, str]]:
        """
        Searches the memory for similar documents.
        """
        if not self.documents:
            return []
            
        query_embedding = self.model.encode([query])
        distances, indices = self.index.search(np.array(query_embedding, dtype=np.float32), k)
        
        results = []
        for i, dist in enumerate(distances[0]):
            if indices[0][i] != -1:
                results.append((dist, self.documents[indices[0][i]]))
        
        return results

memory_instance = Memory()
