"""
Vector store management using ChromaDB
Supports two-tier document system: core (protected) and user (manageable)
"""
import chromadb
from chromadb.config import Settings
from chromadb.utils import embedding_functions
from typing import List, Dict, Optional
from app.core.config import settings
import uuid

class VectorStore:
    """Manages vector database operations with core/user document separation"""

    def __init__(self):
        """Initialize ChromaDB client"""
        self.client = chromadb.PersistentClient(
            path=settings.CHROMA_PERSIST_DIRECTORY,
            settings=Settings(
                anonymized_telemetry=False,
                allow_reset=True
            )
        )

        # Configure embedding function based on settings
        if settings.EMBEDDING_PROVIDER == "openai":
            self.embedding_function = embedding_functions.OpenAIEmbeddingFunction(
                api_key=settings.OPENAI_API_KEY,
                model_name=settings.EMBEDDING_MODEL
            )
        else:
            # Use default sentence-transformers
            self.embedding_function = embedding_functions.DefaultEmbeddingFunction()

        # Try to get existing collection
        try:
            self.collection = self.client.get_collection(
                name=settings.CHROMA_COLLECTION_NAME,
                embedding_function=self.embedding_function
            )
        except Exception:
            # Collection doesn't exist or has wrong embedding function, create new one
            try:
                # Delete if exists with wrong config
                self.client.delete_collection(settings.CHROMA_COLLECTION_NAME)
            except:
                pass

            # Create collection with correct embedding function
            self.collection = self.client.create_collection(
                name=settings.CHROMA_COLLECTION_NAME,
                metadata={"hnsw:space": "cosine"},  # Use cosine similarity
                embedding_function=self.embedding_function
            )

    def add_documents(
        self,
        documents: List[str],
        metadatas: List[Dict],
        ids: Optional[List[str]] = None
    ) -> List[str]:
        """
        Add documents to vector store
        Metadata should include: document_id, scope ('core' or 'user'), user_id (if user scope)

        Args:
            documents: List of text chunks
            metadatas: List of metadata dicts for each chunk
            ids: Optional list of IDs (generated if not provided)

        Returns:
            List of document IDs
        """
        if ids is None:
            ids = [str(uuid.uuid4()) for _ in documents]

        # Validate scope in metadata
        for meta in metadatas:
            if "scope" not in meta:
                meta["scope"] = "user"  # Default to user scope
            if meta["scope"] not in ["core", "user"]:
                raise ValueError(f"Invalid scope: {meta['scope']}. Must be 'core' or 'user'")

        self.collection.add(
            documents=documents,
            metadatas=metadatas,
            ids=ids
        )

        return ids

    def search(
        self,
        query: str,
        n_results: int = None,
        user_id: Optional[str] = None,
        include_core: bool = True
    ) -> Dict:
        """
        Search for similar documents across core and user documents

        Args:
            query: Search query text
            n_results: Number of results to return
            user_id: User ID to filter user-specific documents
            include_core: Whether to include core documents in search

        Returns:
            Dict with documents, metadatas, distances, and ids
        """
        if n_results is None:
            n_results = settings.TOP_K_RETRIEVAL

        # Build filter for core and user documents
        where_filter = None
        if user_id and include_core:
            # Search both core docs and user's docs
            # ChromaDB doesn't support OR directly, so we'll do two queries and merge
            core_results = self.collection.query(
                query_texts=[query],
                n_results=n_results,
                where={"scope": "core"}
            )

            user_results = self.collection.query(
                query_texts=[query],
                n_results=n_results,
                where={"scope": "user", "user_id": user_id}
            )

            # Merge and sort by distance
            return self._merge_results(core_results, user_results, n_results)

        elif user_id and not include_core:
            # Only user documents
            where_filter = {"scope": "user", "user_id": user_id}
        elif include_core and not user_id:
            # Only core documents
            where_filter = {"scope": "core"}

        results = self.collection.query(
            query_texts=[query],
            n_results=n_results,
            where=where_filter
        )

        return {
            "documents": results["documents"][0] if results["documents"] else [],
            "metadatas": results["metadatas"][0] if results["metadatas"] else [],
            "distances": results["distances"][0] if results["distances"] else [],
            "ids": results["ids"][0] if results["ids"] else []
        }

    def _merge_results(self, results1: Dict, results2: Dict, n_results: int) -> Dict:
        """Merge two query results and return top n by distance"""
        docs = (results1["documents"][0] if results1["documents"] else []) + \
               (results2["documents"][0] if results2["documents"] else [])
        metas = (results1["metadatas"][0] if results1["metadatas"] else []) + \
                (results2["metadatas"][0] if results2["metadatas"] else [])
        dists = (results1["distances"][0] if results1["distances"] else []) + \
                (results2["distances"][0] if results2["distances"] else [])
        ids = (results1["ids"][0] if results1["ids"] else []) + \
              (results2["ids"][0] if results2["ids"] else [])

        # Sort by distance and take top n
        if dists:
            sorted_indices = sorted(range(len(dists)), key=lambda i: dists[i])[:n_results]
            return {
                "documents": [docs[i] for i in sorted_indices],
                "metadatas": [metas[i] for i in sorted_indices],
                "distances": [dists[i] for i in sorted_indices],
                "ids": [ids[i] for i in sorted_indices]
            }

        return {"documents": [], "metadatas": [], "distances": [], "ids": []}

    def delete_by_document_id(self, document_id: str, user_id: Optional[str] = None):
        """
        Delete all chunks belonging to a document
        If user_id provided, only deletes user documents (protects core docs)
        """
        if user_id:
            # Only allow deletion of user's own documents
            self.collection.delete(
                where={"document_id": document_id, "scope": "user", "user_id": user_id}
            )
        else:
            # Dev/admin can delete any document
            self.collection.delete(
                where={"document_id": document_id}
            )

    def delete_by_ids(self, ids: List[str]):
        """Delete specific chunks by their IDs"""
        self.collection.delete(ids=ids)

    def get_collection_count(self) -> int:
        """Get total number of chunks in collection"""
        return self.collection.count()

    def get_user_document_count(self, user_id: str) -> int:
        """Get number of chunks for a specific user"""
        results = self.collection.get(
            where={"scope": "user", "user_id": user_id}
        )
        return len(results["ids"]) if results["ids"] else 0

    def get_core_document_count(self) -> int:
        """Get number of core document chunks"""
        results = self.collection.get(
            where={"scope": "core"}
        )
        return len(results["ids"]) if results["ids"] else 0

    def reset_collection(self):
        """Delete all data in collection (use with caution!)"""
        self.client.delete_collection(settings.CHROMA_COLLECTION_NAME)
        self.collection = self.client.create_collection(
            name=settings.CHROMA_COLLECTION_NAME,
            metadata={"hnsw:space": "cosine"},
            embedding_function=self.embedding_function
        )
