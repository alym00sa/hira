"""
Document Service - Handles document uploads and management
"""
from typing import Dict, List, Optional
from fastapi import UploadFile
from pathlib import Path
import uuid
import shutil
import json
from datetime import datetime
from app.rag.rag_engine import RAGEngine
from app.core.config import settings

class DocumentService:
    """Manages document uploads and processing"""

    def __init__(self):
        self.rag_engine = RAGEngine()
        self.upload_dir = Path(settings.UPLOAD_DIR)
        self.upload_dir.mkdir(parents=True, exist_ok=True)

        # Metadata store (use DB in production)
        self.metadata_file = self.upload_dir / "documents_metadata.json"
        self.metadata = self._load_metadata()

    def _load_metadata(self) -> Dict:
        """Load document metadata from file"""
        if self.metadata_file.exists():
            with open(self.metadata_file, 'r') as f:
                return json.load(f)
        return {}

    def _save_metadata(self):
        """Save document metadata to file"""
        with open(self.metadata_file, 'w') as f:
            json.dump(self.metadata, f, indent=2, default=str)

    async def process_upload(
        self,
        file: UploadFile,
        user_id: Optional[str] = None,
        scope: str = "user"
    ) -> Dict:
        """
        Process an uploaded document

        Args:
            file: Uploaded file
            user_id: User ID (required for user scope)
            scope: 'core' or 'user'

        Returns:
            Dict with upload results
        """
        # Validate file
        self._validate_file(file)

        # Generate document ID
        document_id = str(uuid.uuid4())

        # Create user directory if needed
        if scope == "user" and user_id:
            user_dir = self.upload_dir / user_id
            user_dir.mkdir(parents=True, exist_ok=True)
            save_path = user_dir / f"{document_id}_{file.filename}"
        else:
            save_path = self.upload_dir / f"{document_id}_{file.filename}"

        # Save file to disk
        try:
            with open(save_path, "wb") as buffer:
                shutil.copyfileobj(file.file, buffer)
        finally:
            file.file.close()

        file_size = save_path.stat().st_size

        # Process document through RAG pipeline
        try:
            with open(save_path, "rb") as f:
                ingestion_result = self.rag_engine.ingest_document(
                    file_obj=f,
                    filename=file.filename,
                    scope=scope,
                    user_id=user_id
                )

            # Store metadata
            self.metadata[document_id] = {
                "document_id": document_id,
                "filename": file.filename,
                "original_filename": file.filename,
                "file_path": str(save_path),
                "file_size": file_size,
                "upload_date": datetime.now().isoformat(),
                "document_type": save_path.suffix,
                "scope": scope,
                "user_id": user_id,
                "processed": True,
                "chunk_count": ingestion_result["chunk_count"]
            }
            self._save_metadata()

            return {
                "document_id": document_id,
                "filename": file.filename,
                "file_size": file_size,
                "document_type": save_path.suffix,
                "processed": True,
                "chunk_count": ingestion_result["chunk_count"]
            }

        except Exception as e:
            # Clean up file if processing failed
            if save_path.exists():
                save_path.unlink()
            raise Exception(f"Document processing failed: {str(e)}")

    async def list_documents(
        self,
        user_id: Optional[str] = None,
        include_core: bool = True
    ) -> List[Dict]:
        """
        List documents

        Args:
            user_id: Filter by user ID
            include_core: Whether to include core documents

        Returns:
            List of document metadata
        """
        documents = []

        for doc_id, meta in self.metadata.items():
            # Filter logic
            if user_id and meta.get("scope") == "user":
                if meta.get("user_id") == user_id:
                    documents.append(meta)
            elif include_core and meta.get("scope") == "core":
                documents.append(meta)
            elif not user_id and not include_core:
                # Show all user documents if no user filter
                if meta.get("scope") == "user":
                    documents.append(meta)

        # Sort by upload date (newest first)
        documents.sort(key=lambda x: x.get("upload_date", ""), reverse=True)

        return documents

    async def get_document(self, document_id: str) -> Optional[Dict]:
        """Get document metadata by ID"""
        return self.metadata.get(document_id)

    async def delete_document(
        self,
        document_id: str,
        user_id: Optional[str] = None
    ):
        """
        Delete a document

        Args:
            document_id: Document ID to delete
            user_id: User ID (prevents deletion of core docs and other users' docs)
        """
        if document_id not in self.metadata:
            raise ValueError(f"Document not found: {document_id}")

        meta = self.metadata[document_id]

        # Protect core documents from user deletion
        if user_id and meta.get("scope") == "core":
            raise PermissionError("Cannot delete core knowledge base documents")

        # Protect other users' documents
        if user_id and meta.get("user_id") != user_id:
            raise PermissionError("Cannot delete another user's documents")

        # Delete from vector store
        self.rag_engine.delete_document(document_id, user_id)

        # Delete file from disk
        file_path = Path(meta["file_path"])
        if file_path.exists():
            file_path.unlink()

        # Remove from metadata
        del self.metadata[document_id]
        self._save_metadata()

    def _validate_file(self, file: UploadFile):
        """Validate uploaded file"""
        if not file.filename:
            raise ValueError("No filename provided")

        # Check file extension
        file_ext = Path(file.filename).suffix.lower()
        if file_ext not in settings.ALLOWED_EXTENSIONS:
            raise ValueError(
                f"File type not allowed. Supported: {', '.join(settings.ALLOWED_EXTENSIONS)}"
            )

        # Note: FastAPI UploadFile doesn't easily provide size before reading
        # For production, implement streaming validation
