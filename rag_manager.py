from typing import List, Dict, Optional, Tuple
import faiss


class RAGManager:
    """Manages Retrieval-Augmented Generation operations using sentence transformers."""

    def __init__(self, model_name: str='all-MiniLM-L6-v2', index_path:
        Optional[str]=None):
        """
        Initialize the RAG manager.

        Args:
            model_name: Name of the sentence transformer model to use
            index_path: Path to save/load the FAISS index
        """
        self.model_name = model_name
        from vectordb_manager import VectorDBManager
        self.vectordb = VectorDBManager(model_name, index_path)
        self.model = self.vectordb.model
        self.index_path = self.vectordb.index_path
        self.metadata_path = self.vectordb.metadata_path
        self.dimension = self.vectordb.dimension
        self.index = self.vectordb.index
        self.metadata = self.vectordb.metadata

    def add_documents(self, documents: List[str], metadatas: Optional[List[
        Dict]]=None):
        """
        Add documents to the RAG index.

        Args:
            documents: List of text documents to add
            metadatas: Optional list of metadata for each document
        """
        if metadatas is None:
            metadatas = [{}] * len(documents)
        for i, meta in enumerate(metadatas):
            if 'file' not in meta:
                meta['file'] = f'document_{len(self.metadata) + i}'
        self.vectordb.add_documents(documents, metadatas)
        self.metadata = self.vectordb.metadata

    def search(self, query: str, k: int=5) ->List[Tuple[str, float, Dict]]:
        """
        Search for relevant documents.

        Args:
            query: Query string
            k: Number of results to return

        Returns:
            List of (document, score, metadata) tuples
        """
        from vectordb_manager import VectorDBManager
        temp_vdb = VectorDBManager(model_name=self.model_name, index_path=
            self.index_path)
        results = temp_vdb.search(query, k)
        return results

    def get_document_count(self) ->int:
        """Get the number of documents in the index."""
        return len(self.metadata)

    def clear_index(self):
        """Clear the index and metadata."""
        self.index = faiss.IndexFlatIP(self.dimension)
        self.metadata = []
