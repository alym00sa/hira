"""
RAG (Retrieval Augmented Generation) API endpoints
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from app.rag.rag_engine import RAGEngine

router = APIRouter()

# Shared RAG engine instance
_rag_engine = None

def get_rag_engine():
    """Get or create the shared RAG engine instance"""
    global _rag_engine
    if _rag_engine is None:
        _rag_engine = RAGEngine()
    return _rag_engine

class RAGSearchRequest(BaseModel):
    query: str
    n_results: int = 3

class RAGSearchResponse(BaseModel):
    has_context: bool
    context: str
    sources: list

@router.post("/rag/search", response_model=RAGSearchResponse)
async def search_knowledge_base(request: RAGSearchRequest):
    """
    Search the knowledge base and return relevant context
    Used by voice agent for RAG integration
    """
    try:
        rag_engine = get_rag_engine()

        # Build context from RAG
        context_data = rag_engine.build_context_prompt(
            query=request.query,
            n_results=request.n_results
        )

        # Format response
        if context_data.get("has_context"):
            return RAGSearchResponse(
                has_context=True,
                context=context_data.get("context", "")[:1000],  # Limit context size
                sources=[
                    {"filename": src["filename"]}
                    for src in context_data.get("sources", [])[:3]
                ]
            )
        else:
            return RAGSearchResponse(
                has_context=False,
                context="No relevant information found in the knowledge base.",
                sources=[]
            )

    except Exception as e:
        print(f"❌ RAG search error: {e}")
        raise HTTPException(status_code=500, detail=f"RAG search failed: {str(e)}")
