"""
Quick test script to verify RAG retrieval is working
"""
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent))

from app.rag.rag_engine import RAGEngine

def test_rag():
    print("Testing RAG System")
    print("=" * 60)

    # Initialize RAG engine
    rag = RAGEngine()

    # Get stats
    stats = rag.get_stats()
    print(f"\nVector Database Stats:")
    print(f"  Total chunks: {stats['total_chunks']}")
    print(f"  Core chunks: {stats['core_chunks']}")

    # Test query about EU AI Act
    print(f"\nTest Query: 'What is the EU AI Act?'")
    print("-" * 60)

    context = rag.build_context_prompt(
        query="What is the EU AI Act?",
        user_id=None,
        n_results=5
    )

    print(f"\nResults:")
    print(f"  Has context: {context['has_context']}")
    print(f"  Sources found: {len(context['sources'])}")

    if context['sources']:
        print(f"\nTop sources:")
        for i, source in enumerate(context['sources'][:3], 1):
            print(f"\n{i}. {source['filename']}")
            print(f"   Similarity: {source['similarity']:.2%}")
            print(f"   Excerpt: {source['excerpt'][:150]}...")
    else:
        print("\n  WARNING: No sources found!")
        print("\n  This could mean:")
        print("  1. Embedding model not configured (needs OPENAI_API_KEY)")
        print("  2. Similarity threshold too high (currently 0.7)")
        print("  3. Documents not properly embedded")

if __name__ == "__main__":
    test_rag()
