"""
Utility script to load core documents into HiRA's knowledge base
Run this as a developer to populate the core knowledge base

Usage:
    python load_core_docs.py
"""
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent))

from app.rag.rag_engine import RAGEngine
from app.core.config import settings

def load_core_documents():
    """Load all documents from agent-rag-docs as core knowledge"""

    print("=" * 60)
    print("HiRA - Core Knowledge Base Loader")
    print("=" * 60)
    print()

    # Initialize RAG engine
    print("Initializing RAG engine...")
    rag_engine = RAGEngine()

    # Path to core documents
    core_docs_path = Path(__file__).parent.parent / "agent-rag-docs"

    if not core_docs_path.exists():
        print(f"ERROR: Core documents directory not found at: {core_docs_path}")
        print("   Please ensure 'agent-rag-docs' folder exists in the project root")
        return

    print(f"Core documents directory: {core_docs_path}")
    print()

    # Get stats before loading
    stats_before = rag_engine.get_stats()
    print(f"Current RAG stats:")
    print(f"   Total chunks: {stats_before['total_chunks']}")
    print(f"   Core chunks: {stats_before['core_chunks']}")
    print()

    # Load documents
    print("Processing documents...")
    print()

    try:
        results = rag_engine.ingest_directory(
            directory_path=str(core_docs_path),
            scope="core",
            user_id=None
        )

        # Display results
        print()
        print("=" * 60)
        print("Loading Complete!")
        print("=" * 60)
        print()
        print(f"Documents processed: {len(results)}")
        print()

        total_chunks = sum(r["chunk_count"] for r in results)
        print("Document Details:")
        print("-" * 60)
        for i, result in enumerate(results, 1):
            print(f"{i}. {result['filename']}")
            print(f"   Chunks: {result['chunk_count']}")
            print(f"   Document ID: {result['document_id'][:8]}...")
            print()

        # Get stats after loading
        stats_after = rag_engine.get_stats()
        print("=" * 60)
        print(f"Updated RAG stats:")
        print(f"   Total chunks: {stats_after['total_chunks']} (+{stats_after['total_chunks'] - stats_before['total_chunks']})")
        print(f"   Core chunks: {stats_after['core_chunks']} (+{stats_after['core_chunks'] - stats_before['core_chunks']})")
        print()
        print("Core knowledge base is ready!")
        print()

    except Exception as e:
        print()
        print(f"ERROR during loading: {str(e)}")
        print()
        import traceback
        traceback.print_exc()

def reset_core_documents():
    """Reset/clear all core documents (use with caution!)"""

    print("=" * 60)
    print("WARNING: RESET CORE DOCUMENTS")
    print("=" * 60)
    print()
    print("This will DELETE all core documents from the knowledge base.")
    response = input("Are you sure? Type 'YES' to confirm: ")

    if response != "YES":
        print("Reset cancelled.")
        return

    print()
    print("Resetting vector store...")

    rag_engine = RAGEngine()
    rag_engine.vector_store.reset_collection()

    print("Core documents cleared.")
    print()

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Manage HiRA core knowledge base")
    parser.add_argument(
        "--reset",
        action="store_true",
        help="Reset/clear all core documents"
    )

    args = parser.parse_args()

    if args.reset:
        reset_core_documents()
    else:
        load_core_documents()
