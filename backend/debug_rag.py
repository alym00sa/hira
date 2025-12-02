"""
Debug script to check raw RAG retrieval results without filtering
"""
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent))

from app.rag.rag_engine import RAGEngine
from app.core.config import settings

def debug_rag():
    print("Debug RAG Retrieval")
    print("=" * 60)

    rag = RAGEngine()

    # Get stats
    stats = rag.get_stats()
    print(f"\nVector Database Stats:")
    print(f"  Total chunks: {stats['total_chunks']}")
    print(f"  Core chunks: {stats['core_chunks']}")

    # Test query
    query = "What is the EU AI Act?"
    print(f"\nTest Query: '{query}'")
    print("-" * 60)

    # Get raw results from vector store (no filtering)
    results = rag.vector_store.search(
        query=query,
        n_results=10,
        user_id=None,
        include_core=True
    )

    print(f"\nRaw Results (before similarity threshold):")
    print(f"  Documents found: {len(results['documents'])}")
    print(f"  Distances: {results['distances']}")

    if results['documents']:
        print(f"\nTop 5 Results:")
        for i in range(min(5, len(results['documents']))):
            dist = results['distances'][i]
            similarity = 1 - dist
            meta = results['metadatas'][i]
            doc = results['documents'][i]

            print(f"\n{i+1}. {meta['filename']}")
            print(f"   Distance: {dist:.4f}")
            print(f"   Similarity: {similarity:.4f} (threshold: {settings.SIMILARITY_THRESHOLD})")
            print(f"   Passes threshold: {'YES' if similarity >= settings.SIMILARITY_THRESHOLD else 'NO'}")
            print(f"   Excerpt: {doc[:150]}...")
    else:
        print("\n  ERROR: No documents returned at all!")
        print("  This suggests the query embedding or search is failing completely.")

if __name__ == "__main__":
    debug_rag()
