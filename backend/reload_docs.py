"""
Script to reset and reload all documents with proper OpenAI embeddings
"""
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent))

from app.rag.rag_engine import RAGEngine

def main():
    print("=" * 60)
    print("Resetting and Reloading Core Documents")
    print("Using: text-embedding-3-large")
    print("=" * 60)
    print()

    rag_engine = RAGEngine()

    # Reset the collection
    print("Step 1: Clearing existing vector database...")
    rag_engine.vector_store.reset_collection()
    print("  Done! Database cleared.")
    print()

    # Reload documents
    core_docs_path = Path(__file__).parent.parent / "agent-rag-docs"

    if not core_docs_path.exists():
        print(f"ERROR: Documents directory not found: {core_docs_path}")
        return

    print(f"Step 2: Loading documents from: {core_docs_path}")
    print()

    results = rag_engine.ingest_directory(
        directory_path=str(core_docs_path),
        scope="core",
        user_id=None
    )

    print()
    print("=" * 60)
    print("Loading Complete!")
    print("=" * 60)
    print()
    print(f"Documents loaded: {len(results)}")
    print(f"Total chunks: {sum(r['chunk_count'] for r in results)}")
    print()

    print("Document Details:")
    print("-" * 60)
    for i, result in enumerate(results, 1):
        print(f"{i}. {result['filename']}")
        print(f"   Chunks: {result['chunk_count']}")
        print()

    # Get final stats
    stats = rag_engine.get_stats()
    print("=" * 60)
    print(f"Final Vector Database Stats:")
    print(f"  Total chunks: {stats['total_chunks']}")
    print(f"  Core chunks: {stats['core_chunks']}")
    print()
    print("RAG system ready!")

if __name__ == "__main__":
    main()
