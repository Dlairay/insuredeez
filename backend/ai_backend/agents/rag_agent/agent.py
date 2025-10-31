"""
RAG Agent for Policy Document Retrieval
Orchestrates the RAG pipeline and provides a clean interface for policy queries
"""

import os
from typing import List, Dict, Optional
from dotenv import load_dotenv
from .tools import PolicyRAGPipeline

# Load environment variables
load_dotenv()


class RAGAgent:
    """
    Agent that manages policy document retrieval using RAG pipeline.
    Provides high-level interface for embedding and querying policy documents.
    """

    def __init__(
        self,
        policies_dir: str = None,
        chroma_db_path: str = None,
        auto_load: bool = False
    ):
        """
        Initialize the RAG Agent.

        Args:
            policies_dir: Directory containing policy PDF files
            chroma_db_path: Path to ChromaDB database
            auto_load: If True, attempt to load existing vectorstore on init
        """
        # Set default paths if not provided
        if policies_dir is None:
            policies_dir = os.path.join(
                os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
                "policies"
            )

        if chroma_db_path is None:
            chroma_db_path = os.path.join(
                os.path.dirname(__file__),
                "chroma_db"
            )

        # Initialize the RAG pipeline
        self.pipeline = PolicyRAGPipeline(
            policies_dir=policies_dir,
            chroma_db_path=chroma_db_path
        )

        self.is_ready = False

        # Auto-load existing vectorstore if requested
        if auto_load and os.path.exists(chroma_db_path):
            try:
                self.pipeline.load_existing_vectorstore()
                self.is_ready = True
                print("RAG Agent initialized with existing vectorstore")
            except Exception as e:
                print(f"Could not load existing vectorstore: {e}")
                print("You will need to run embed_policies() first")

    def embed_policies(self, force_rebuild: bool = False) -> bool:
        """
        Process and embed all policy documents in the policies directory.

        Args:
            force_rebuild: If True, rebuild even if vectorstore exists

        Returns:
            True if successful, False otherwise
        """
        # Check if vectorstore already exists
        if os.path.exists(self.pipeline.chroma_db_path) and not force_rebuild:
            response = input(
                f"Vectorstore already exists at {self.pipeline.chroma_db_path}. "
                "Rebuild? (y/n): "
            )
            if response.lower() != 'y':
                print("Loading existing vectorstore instead...")
                self.pipeline.load_existing_vectorstore()
                self.is_ready = True
                return True

        try:
            # Run the full pipeline
            self.pipeline.build_pipeline()
            self.is_ready = True
            return True
        except Exception as e:
            print(f"Error embedding policies: {e}")
            return False

    def query_policies(
        self,
        query: str,
        k: int = 4,
        filename: Optional[str] = None,
        include_scores: bool = False
    ) -> List[Dict]:
        """
        Query the policy documents for relevant information.

        Args:
            query: The search query
            k: Number of results to return
            filename: Optional filename to filter results by specific policy
            include_scores: If True, include similarity scores

        Returns:
            List of relevant document chunks with metadata
        """
        if not self.is_ready:
            raise RuntimeError(
                "RAG Agent not ready. Run embed_policies() first or "
                "initialize with auto_load=True"
            )

        if include_scores:
            results = self.pipeline.query_with_scores(
                query_text=query,
                k=k,
                filter_by_filename=filename
            )
            # Format results with scores
            formatted = []
            for doc, score in results:
                formatted.append({
                    "content": doc.page_content,
                    "metadata": doc.metadata,
                    "filename": doc.metadata.get("filename", "unknown"),
                    "page": doc.metadata.get("page", "unknown"),
                    "similarity_score": score
                })
            return formatted
        else:
            return self.pipeline.query(
                query_text=query,
                k=k,
                filter_by_filename=filename
            )

    def get_available_policies(self) -> List[str]:
        """
        Get list of available policy document filenames.

        Returns:
            List of policy filenames
        """
        from pathlib import Path
        policy_files = list(Path(self.pipeline.policies_dir).glob("*.pdf"))
        return [f.name for f in policy_files]

    def search_in_policy(self, policy_name: str, query: str, k: int = 4) -> List[Dict]:
        """
        Search within a specific policy document.

        Args:
            policy_name: Name of the policy file
            query: Search query
            k: Number of results

        Returns:
            List of relevant chunks from the specified policy
        """
        return self.query_policies(query=query, k=k, filename=policy_name)

    def get_policy_context(self, query: str, context_size: int = 3) -> str:
        """
        Get formatted context from policy documents for a query.
        Useful for feeding into LLM prompts.

        Args:
            query: The search query
            context_size: Number of chunks to retrieve

        Returns:
            Formatted string with context from policies
        """
        results = self.query_policies(query=query, k=context_size)

        context_parts = []
        for i, result in enumerate(results, 1):
            context_parts.append(
                f"[Source {i}: {result['filename']}, Page {result['page']}]\n"
                f"{result['content']}\n"
            )

        return "\n---\n".join(context_parts)


def create_rag_agent(auto_load: bool = True) -> RAGAgent:
    """
    Factory function to create a RAG Agent with default settings.

    Args:
        auto_load: If True, attempt to load existing vectorstore

    Returns:
        Initialized RAGAgent instance
    """
    return RAGAgent(auto_load=auto_load)
