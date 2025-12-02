"""
RAG Engine - Orchestrates retrieval and context generation
"""
from typing import List, Dict, Optional
from app.rag.vector_store import VectorStore
from app.rag.document_processor import DocumentProcessor
from app.core.config import settings

class RAGEngine:
    """Main RAG orchestration engine"""

    def __init__(self):
        self.vector_store = VectorStore()
        self.document_processor = DocumentProcessor()

    def ingest_document(
        self,
        file_path: str = None,
        file_obj = None,
        filename: str = None,
        scope: str = "user",
        user_id: str = None
    ) -> Dict:
        """
        Ingest a document into the RAG system

        Args:
            file_path: Path to file
            file_obj: File-like object
            filename: Original filename
            scope: 'core' or 'user'
            user_id: User ID (required for user scope)

        Returns:
            Dict with ingestion results
        """
        # Process document into chunks
        processed = self.document_processor.process_document(
            file_path=file_path,
            file_obj=file_obj,
            filename=filename,
            scope=scope,
            user_id=user_id
        )

        # Add to vector store (ChromaDB handles embedding internally)
        chunk_ids = self.vector_store.add_documents(
            documents=processed["chunks"],
            metadatas=processed["metadata"]
        )

        return {
            "document_id": processed["document_id"],
            "filename": processed["filename"],
            "chunk_count": processed["chunk_count"],
            "chunk_ids": chunk_ids,
            "scope": scope,
            "user_id": user_id
        }

    def ingest_directory(
        self,
        directory_path: str,
        scope: str = "core",
        user_id: str = None
    ) -> List[Dict]:
        """
        Ingest all documents from a directory (useful for core docs)

        Args:
            directory_path: Path to directory
            scope: 'core' or 'user'
            user_id: User ID (if scope is user)

        Returns:
            List of ingestion results
        """
        processed_docs = self.document_processor.process_directory(
            directory_path=directory_path,
            scope=scope,
            user_id=user_id
        )

        results = []
        for doc in processed_docs:
            chunk_ids = self.vector_store.add_documents(
                documents=doc["chunks"],
                metadatas=doc["metadata"]
            )

            results.append({
                "document_id": doc["document_id"],
                "filename": doc["filename"],
                "chunk_count": doc["chunk_count"],
                "chunk_ids": chunk_ids,
                "scope": scope
            })

        return results

    def retrieve_context(
        self,
        query: str,
        user_id: Optional[str] = None,
        n_results: int = None,
        include_core: bool = True
    ) -> Dict:
        """
        Retrieve relevant context for a query

        Args:
            query: User's question/query
            user_id: User ID to include user-specific docs
            n_results: Number of results to retrieve
            include_core: Whether to include core documents

        Returns:
            Dict with context chunks and metadata
        """
        if n_results is None:
            n_results = settings.TOP_K_RETRIEVAL

        # Search vector store
        results = self.vector_store.search(
            query=query,
            n_results=n_results,
            user_id=user_id,
            include_core=include_core
        )

        # Format results with relevance filtering
        filtered_chunks = []
        for i, (doc, meta, dist) in enumerate(zip(
            results["documents"],
            results["metadatas"],
            results["distances"]
        )):
            # Convert distance to similarity score (0-1, higher is better)
            # ChromaDB uses cosine distance, so similarity = 1 - distance
            similarity = 1 - dist

            # Filter by similarity threshold
            if similarity >= settings.SIMILARITY_THRESHOLD:
                filtered_chunks.append({
                    "content": doc,
                    "metadata": meta,
                    "similarity": similarity,
                    "rank": i + 1
                })

        return {
            "chunks": filtered_chunks,
            "total_found": len(filtered_chunks),
            "query": query
        }

    def build_context_prompt(
        self,
        query: str,
        user_id: Optional[str] = None,
        n_results: int = None
    ) -> Dict:
        """
        Build a formatted context prompt for the LLM

        Args:
            query: User's question
            user_id: User ID
            n_results: Number of chunks to retrieve

        Returns:
            Dict with formatted context and sources
        """
        # Retrieve relevant context
        context_data = self.retrieve_context(
            query=query,
            user_id=user_id,
            n_results=n_results
        )

        if not context_data["chunks"]:
            return {
                "context": "No relevant information found in the knowledge base.",
                "sources": [],
                "has_context": False
            }

        # Build context string with citations
        context_parts = []
        sources = []

        for chunk in context_data["chunks"]:
            content = chunk["content"]
            meta = chunk["metadata"]

            # Format source citation
            source_type = "core knowledge base" if meta["scope"] == "core" else "your uploaded documents"
            page_info = f", Page {meta.get('page_number', 'N/A')}" if "page_number" in meta else ""

            context_parts.append(
                f"[From {meta['filename']}{page_info}]:\n{content}\n"
            )

            # Add to sources list for response metadata
            sources.append({
                "filename": meta["filename"],
                "scope": meta["scope"],
                "page_number": meta.get("page_number"),
                "similarity": chunk["similarity"],
                "excerpt": content[:200] + "..." if len(content) > 200 else content
            })

        context_string = "\n---\n".join(context_parts)

        return {
            "context": context_string,
            "sources": sources,
            "has_context": True,
            "chunk_count": len(context_data["chunks"])
        }

    def delete_document(
        self,
        document_id: str,
        user_id: Optional[str] = None
    ):
        """
        Delete a document from the RAG system
        If user_id is provided, only user documents can be deleted (protects core docs)

        Args:
            document_id: Document ID to delete
            user_id: User ID (to prevent deleting core docs)
        """
        self.vector_store.delete_by_document_id(document_id, user_id)

    def get_stats(self) -> Dict:
        """Get RAG system statistics"""
        return {
            "total_chunks": self.vector_store.get_collection_count(),
            "core_chunks": self.vector_store.get_core_document_count(),
            "vector_db": "ChromaDB",
            "status": "operational"
        }

    def get_user_stats(self, user_id: str) -> Dict:
        """Get statistics for a specific user"""
        return {
            "user_id": user_id,
            "user_chunks": self.vector_store.get_user_document_count(user_id),
            "total_chunks": self.vector_store.get_collection_count()
        }
