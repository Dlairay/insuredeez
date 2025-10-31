"""
Embedding Pipeline Script
Loads and embeds all policy PDF documents into ChromaDB vector store
Run this FIRST before running taxonomy filling
"""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent.parent))

from agents.rag_agent import RAGAgent


def main():
    """Main execution function for embedding policies"""
    print("\n" + "="*70)
    print("POLICY EMBEDDING PIPELINE")
    print("="*70)

    print("\nThis script will:")
    print("1. Load all PDF files from policies/ directory")
    print("2. Extract text and chunk documents")
    print("3. Generate OpenAI embeddings")
    print("4. Store in ChromaDB vector database")

    # Initialize RAG agent
    print("\nInitializing RAG Agent...")
    agent = RAGAgent()

    # Check available policies
    policies = agent.get_available_policies()
    print(f"\nFound {len(policies)} policy documents:")
    for i, policy in enumerate(policies, 1):
        print(f"  {i}. {policy}")

    # Ask for confirmation
    print("\n" + "-"*70)
    print("ChromaDB will be created at:")
    print(f"  {agent.pipeline.chroma_db_path}")
    print("-"*70)

    # Check if already exists
    chroma_path = Path(agent.pipeline.chroma_db_path)
    if chroma_path.exists():
        print("\n⚠ ChromaDB already exists!")
        choice = input("Do you want to rebuild? (y/n): ").strip().lower()
        if choice != 'y':
            print("\nCancelled. Using existing ChromaDB.")
            return
        force_rebuild = True
    else:
        choice = input("\nProceed with embedding? (y/n): ").strip().lower()
        if choice != 'y':
            print("\nCancelled.")
            return
        force_rebuild = False

    # Run embedding
    print("\n" + "="*70)
    print("Starting Embedding Process...")
    print("="*70)

    success = agent.embed_policies(force_rebuild=force_rebuild)

    if success:
        print("\n" + "="*70)
        print("✓ EMBEDDING COMPLETED SUCCESSFULLY!")
        print("="*70)
        print(f"\nChromaDB created at: {agent.pipeline.chroma_db_path}")
        print("\nNext step:")
        print("  Run 'python run_retrieval.py' to fill taxonomy conditions")
    else:
        print("\n" + "="*70)
        print("✗ EMBEDDING FAILED")
        print("="*70)
        print("\nPlease check:")
        print("  1. PDF files exist in policies/ directory")
        print("  2. OPENAI_API_KEY is set in .env")
        print("  3. Dependencies are installed (pip install -r requirements.txt)")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nInterrupted by user. Exiting...")
    except Exception as e:
        print(f"\n✗ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
