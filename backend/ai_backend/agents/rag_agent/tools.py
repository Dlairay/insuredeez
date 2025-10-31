"""
RAG Tools for Policy Document Processing
Handles document loading, chunking, embedding, and retrieval using LangChain, ChromaDB, and OpenAI
Now uses unstructured.io for table-aware PDF parsing
"""

import os
from pathlib import Path
from typing import List, Dict, Optional
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores import Chroma
from langchain_core.documents import Document
from unstructured.partition.pdf import partition_pdf


class PolicyRAGPipeline:
    """
    RAG pipeline for processing and embedding policy documents.
    Uses ChromaDB for vector storage and OpenAI for embeddings.
    """

    def __init__(
        self,
        policies_dir: str,
        chroma_db_path: str = "./chroma_db",
        collection_name: str = "policy_documents",
        chunk_size: int = 1000,
        chunk_overlap: int = 200,
        embedding_model: str = "text-embedding-3-small"
    ):
        """
        Initialize the RAG pipeline.

        Args:
            policies_dir: Directory containing policy PDF files
            chroma_db_path: Path to store ChromaDB database
            collection_name: Name of the ChromaDB collection
            chunk_size: Size of text chunks for splitting
            chunk_overlap: Overlap between chunks
            embedding_model: OpenAI embedding model to use
        """
        self.policies_dir = Path(policies_dir)
        self.chroma_db_path = chroma_db_path
        self.collection_name = collection_name
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap

        # Initialize OpenAI embeddings
        self.embeddings = OpenAIEmbeddings(
            model=embedding_model,
            openai_api_key=os.getenv("OPENAI_API_KEY")
        )

        # Initialize text splitter with larger chunks for better context
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=2000,  # Larger chunks to preserve context
            chunk_overlap=400,  # More overlap to not lose connections
            length_function=len,
            separators=["\n\n", "\n", " ", ""]
        )

        # Initialize vector store (will be set during processing)
        self.vectorstore = None

    def load_policy_documents(self) -> List[Document]:
        """
        Load all PDF policy documents from the policies directory using unstructured.io.
        This preserves table structure and provides better text extraction.

        Returns:
            List of LangChain Document objects with metadata
        """
        documents = []
        pdf_files = list(self.policies_dir.glob("*.pdf"))

        if not pdf_files:
            raise ValueError(f"No PDF files found in {self.policies_dir}")

        print(f"Found {len(pdf_files)} policy documents to process:")

        for pdf_path in pdf_files:
            print(f"  - Loading: {pdf_path.name} (with table preservation)")

            try:
                # Use unstructured.io for better PDF parsing
                # Using "fast" strategy - still detects tables but much faster than "hi_res"
                elements = partition_pdf(
                    filename=str(pdf_path),
                    strategy="fast",  # Fast extraction, still detects tables
                    infer_table_structure=True  # Preserve table layout
                )

                # Combine small consecutive elements on same page to avoid tiny chunks
                current_page = None
                current_content = []
                current_type = None

                for element in elements:
                    page_num = element.metadata.page_number

                    # For tables, always keep separate (don't combine)
                    if element.category == "Table":
                        # First, save any accumulated content
                        if current_content:
                            doc = Document(
                                page_content="\n\n".join(current_content),
                                metadata={
                                    "filename": pdf_path.name,
                                    "source_path": str(pdf_path),
                                    "page": current_page,
                                    "type": current_type
                                }
                            )
                            documents.append(doc)
                            current_content = []

                        # Add table as separate document
                        content = element.metadata.text_as_html or element.text
                        doc = Document(
                            page_content=content,
                            metadata={
                                "filename": pdf_path.name,
                                "source_path": str(pdf_path),
                                "page": page_num,
                                "type": "Table"
                            }
                        )
                        documents.append(doc)
                        current_page = None
                        current_type = None

                    else:
                        # For text elements, combine consecutive ones on same page
                        if page_num == current_page:
                            current_content.append(element.text)
                        else:
                            # Page changed - save accumulated content
                            if current_content:
                                doc = Document(
                                    page_content="\n\n".join(current_content),
                                    metadata={
                                        "filename": pdf_path.name,
                                        "source_path": str(pdf_path),
                                        "page": current_page,
                                        "type": current_type or "Text"
                                    }
                                )
                                documents.append(doc)

                            # Start new page
                            current_page = page_num
                            current_content = [element.text]
                            current_type = element.category

                # Don't forget last accumulated content
                if current_content:
                    doc = Document(
                        page_content="\n\n".join(current_content),
                        metadata={
                            "filename": pdf_path.name,
                            "source_path": str(pdf_path),
                            "page": current_page,
                            "type": current_type or "Text"
                        }
                    )
                    documents.append(doc)

                print(f"    Loaded {len([e for e in elements])} elements from {pdf_path.name}")
                table_count = len([e for e in elements if e.category == "Table"])
                if table_count > 0:
                    print(f"    Found {table_count} tables (preserved as HTML)")

            except Exception as e:
                print(f"    Error loading {pdf_path.name}: {str(e)}")
                continue

        print(f"\nTotal documents loaded: {len(documents)}")
        return documents

    def chunk_documents(self, documents: List[Document]) -> List[Document]:
        """
        Split documents into smaller chunks with table preservation.
        Tables are kept whole, narrative text is chunked normally.

        Args:
            documents: List of Document objects to chunk

        Returns:
            List of chunked Document objects with preserved metadata
        """
        print(f"\nChunking {len(documents)} documents (table-aware)...")
        chunked_docs = []
        tables_kept_whole = 0
        text_chunks_created = 0

        for doc in documents:
            if doc.metadata.get("type") == "Table":
                # Keep tables whole - don't split them
                chunked_docs.append(doc)
                tables_kept_whole += 1
            else:
                # Split narrative text normally
                chunks = self.text_splitter.split_documents([doc])
                chunked_docs.extend(chunks)
                text_chunks_created += len(chunks)

        print(f"Created {len(chunked_docs)} total chunks:")
        print(f"  - {tables_kept_whole} tables kept whole")
        print(f"  - {text_chunks_created} text chunks created")
        return chunked_docs

    def create_vector_store(self, documents: List[Document]) -> Chroma:
        """
        Create ChromaDB vector store from documents.

        Args:
            documents: List of chunked Document objects

        Returns:
            ChromaDB vector store
        """
        print(f"\nCreating vector store with {len(documents)} chunks...")

        # Create ChromaDB vector store
        vectorstore = Chroma.from_documents(
            documents=documents,
            embedding=self.embeddings,
            collection_name=self.collection_name,
            persist_directory=self.chroma_db_path
        )

        print(f"Vector store created and persisted to {self.chroma_db_path}")
        return vectorstore

    def build_pipeline(self) -> Chroma:
        """
        Execute the full RAG pipeline: load, chunk, and embed documents.

        Returns:
            ChromaDB vector store ready for retrieval
        """
        print("=" * 60)
        print("Starting RAG Pipeline for Policy Documents")
        print("=" * 60)

        # Step 1: Load policy documents
        documents = self.load_policy_documents()

        # Step 2: Chunk documents
        chunked_docs = self.chunk_documents(documents)

        # Step 3: Create vector store and embed
        self.vectorstore = self.create_vector_store(chunked_docs)

        print("\n" + "=" * 60)
        print("RAG Pipeline Complete!")
        print("=" * 60)

        return self.vectorstore

    def load_existing_vectorstore(self) -> Chroma:
        """
        Load an existing ChromaDB vector store.

        Returns:
            ChromaDB vector store
        """
        if not os.path.exists(self.chroma_db_path):
            raise ValueError(f"Vector store not found at {self.chroma_db_path}")

        self.vectorstore = Chroma(
            collection_name=self.collection_name,
            embedding_function=self.embeddings,
            persist_directory=self.chroma_db_path
        )

        print(f"Loaded existing vector store from {self.chroma_db_path}")
        return self.vectorstore

    def query(
        self,
        query_text: str,
        k: int = 4,
        filter_by_filename: Optional[str] = None
    ) -> List[Dict]:
        """
        Query the vector store for relevant policy information.

        Args:
            query_text: The query string
            k: Number of results to return
            filter_by_filename: Optional filename to filter results

        Returns:
            List of relevant document chunks with metadata
        """
        if self.vectorstore is None:
            raise ValueError("Vector store not initialized. Run build_pipeline() first.")

        # Build filter if filename specified
        where_filter = None
        if filter_by_filename:
            where_filter = {"filename": filter_by_filename}

        # Perform similarity search
        if where_filter:
            results = self.vectorstore.similarity_search(
                query_text,
                k=k,
                filter=where_filter
            )
        else:
            results = self.vectorstore.similarity_search(query_text, k=k)

        # Format results
        formatted_results = []
        for doc in results:
            formatted_results.append({
                "content": doc.page_content,
                "metadata": doc.metadata,
                "filename": doc.metadata.get("filename", "unknown"),
                "page": doc.metadata.get("page", "unknown")
            })

        return formatted_results

    def query_with_scores(
        self,
        query_text: str,
        k: int = 4,
        filter_by_filename: Optional[str] = None
    ) -> List[tuple]:
        """
        Query with similarity scores.

        Args:
            query_text: The query string
            k: Number of results to return
            filter_by_filename: Optional filename to filter results

        Returns:
            List of (Document, score) tuples
        """
        if self.vectorstore is None:
            raise ValueError("Vector store not initialized. Run build_pipeline() first.")

        where_filter = None
        if filter_by_filename:
            where_filter = {"filename": filter_by_filename}

        if where_filter:
            results = self.vectorstore.similarity_search_with_score(
                query_text,
                k=k,
                filter=where_filter
            )
        else:
            results = self.vectorstore.similarity_search_with_score(query_text, k=k)

        return results


def initialize_rag_pipeline(
    policies_dir: str = "/Users/ray/Desktop/hackdeez/backend/ai_backend/policies",
    chroma_db_path: str = "/Users/ray/Desktop/hackdeez/backend/ai_backend/agents/rag_agent/chroma_db"
) -> PolicyRAGPipeline:
    """
    Helper function to initialize the RAG pipeline with default settings.

    Args:
        policies_dir: Directory containing policy PDF files
        chroma_db_path: Path to store ChromaDB database

    Returns:
        Initialized PolicyRAGPipeline instance
    """
    return PolicyRAGPipeline(
        policies_dir=policies_dir,
        chroma_db_path=chroma_db_path
    )
