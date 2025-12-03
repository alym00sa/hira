"""
Document management endpoints
"""
from fastapi import APIRouter, UploadFile, File, HTTPException, Depends
from app.models.schemas import DocumentUploadResponse, DocumentListResponse, DocumentMetadata
from app.services.document_service import DocumentService
from datetime import datetime
import uuid

router = APIRouter()

def get_document_service() -> DocumentService:
    """Dependency to get document service instance"""
    return DocumentService()

@router.post("/documents/upload", response_model=DocumentUploadResponse)
async def upload_document(
    file: UploadFile = File(...),
    document_service: DocumentService = Depends(get_document_service)
):
    """
    Upload a document to be processed and added to the RAG knowledge base

    - **file**: PDF, DOCX, TXT, or MD file
    """
    try:
        # Validate file
        if not file.filename:
            raise HTTPException(status_code=400, detail="No filename provided")

        # Process upload as core organizational document
        result = await document_service.process_upload(file, scope="core")

        return DocumentUploadResponse(
            document_id=result["document_id"],
            filename=result["filename"],
            status="processing" if not result.get("processed") else "completed",
            message="Document uploaded and queued for processing",
            metadata=DocumentMetadata(
                filename=result["filename"],
                file_size=result["file_size"],
                upload_date=datetime.now(),
                document_type=result["document_type"],
                processed=result.get("processed", False),
                chunk_count=result.get("chunk_count")
            )
        )

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")

@router.get("/documents", response_model=DocumentListResponse)
async def list_documents(
    document_service: DocumentService = Depends(get_document_service)
):
    """Get list of all uploaded documents"""
    try:
        documents = await document_service.list_documents()
        return DocumentListResponse(
            documents=documents,
            total=len(documents)
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to list documents: {str(e)}")

@router.delete("/documents/{document_id}")
async def delete_document(
    document_id: str,
    document_service: DocumentService = Depends(get_document_service)
):
    """Delete a document from the knowledge base"""
    try:
        await document_service.delete_document(document_id)
        return {"status": "success", "message": f"Document {document_id} deleted"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete document: {str(e)}")

@router.get("/documents/{document_id}")
async def get_document(
    document_id: str,
    document_service: DocumentService = Depends(get_document_service)
):
    """Get details about a specific document"""
    try:
        document = await document_service.get_document(document_id)
        if not document:
            raise HTTPException(status_code=404, detail="Document not found")
        return document
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve document: {str(e)}")
