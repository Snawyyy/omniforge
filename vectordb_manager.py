import os
import json
import hashlib
from typing import List, Dict, Optional, Tuple
from sentence_transformers import SentenceTransformer
import numpy as np
import faiss
from pathlib import Path


class VectorDBManager:
    """Manages vector database operations for RAG using sentence transformers and FAISS."""

    def __init__(self, model_name: str='all-MiniLM-L6-v2', index_path:
        Optional[str]=None):
        """
        Initialize the VectorDB manager.

        Args:
            model_name: Name of the sentence transformer model to use
            index_path: Path to save/load the FAISS index
        """
        self.model = SentenceTransformer(model_name)
        self.index_path = index_path or 'vectordb_index.bin'
        self.metadata_path = self.index_path.replace('.bin', '_metadata.json')
        self.dimension = self.model.get_sentence_embedding_dimension()
        self.index = None
        self.metadata: List[Dict] = []
        self._initialize_index()

    def _initialize_index(self):
        """Initialize or load the FAISS index."""
        if os.path.exists(self.index_path) and os.path.exists(self.
            metadata_path):
            self.index = faiss.read_index(self.index_path)
            with open(self.metadata_path, 'r') as f:
                self.metadata = json.load(f)
        else:
            self.index = faiss.IndexFlatIP(self.dimension)
            self.metadata = []

    def add_documents(self, documents: List[str], metadatas: Optional[List[
        Dict]]=None):
        """
        Add documents to the vector database.

        Args:
            documents: List of text documents to add
            metadatas: Optional list of metadata for each document
        """
        if metadatas is None:
            metadatas = [{}] * len(documents)
        embeddings = self.model.encode(documents)
        faiss.normalize_L2(embeddings)
        self.index.add(embeddings.astype(np.float32))
        for i, meta in enumerate(metadatas):
            doc_hash = hashlib.md5(documents[i].encode()).hexdigest()
            meta_entry = {'id': len(self.metadata), 'hash': doc_hash,
                'content': documents[i], **meta}
            self.metadata.append(meta_entry)
        self._save_index()

    def search(self, query: str, k: int=5) ->List[Tuple[str, float, Dict]]:
        """
        Search for relevant documents.

        Args:
            query: Query string
            k: Number of results to return

        Returns:
            List of (document, score, metadata) tuples
        """
        query_embedding = self.model.encode([query])
        faiss.normalize_L2(query_embedding)
        scores, indices = self.index.search(query_embedding.astype(np.
            float32), k)
        results = []
        for score, idx in zip(scores[0], indices[0]):
            if idx < len(self.metadata):
                doc_info = self.metadata[idx]
                results.append((doc_info['content'], float(score), doc_info))
        return results

    def _save_index(self):
        """Save the FAISS index and metadata to disk."""
        faiss.write_index(self.index, self.index_path)
        with open(self.metadata_path, 'w') as f:
            json.dump(self.metadata, f, indent=2)

    def get_document_count(self) ->int:
        """Get the number of documents in the index."""
        return len(self.metadata)

    def clear_index(self):
        """Clear the index and metadata."""
        self.index = faiss.IndexFlatIP(self.dimension)
        self.metadata = []
        self._save_index()
