Instructions to always follow.

1. Always use think mode.
2. All unique agents should have their own file structure <role>_agent/ agent.py prompt.py tools.py
3.  When improvement/fix is suggested, please look for existing code that it was meant to replace and replace it in its respective files instead of bloating up the codebase, creating dead code that snowballs. All deleted code should be logged into a file called deleted.py with each deletion labelled with where it was from and what it was for, so that changes can be rolled back if needed.
4. Always follow standard practices of separation of concerns where each file, class, and function is meant for a specific purpose
5. When dealing with google adk,always use context7
6. Never make a huge change with massive cascading effects without consulting me.
7. Don't make so many .md files after every change, just update claude md of what was changed, and the latest version. All old functionalities should have been recorded in delete.py anyway.
8. Claude.md should contain the file structure, with annotations of what each file is for, as well as the pipeline design of how the codebasee works.
9. Please don't keep creating a md file every time you do a change, it should be in the deleted.py anyway
10. The instructions mentioned above must never be deleted

---

## File Structure

```
ai_backend/
├── .env                          # Environment variables (API keys)
├── main.py                       # Main entry point
├── CLAUDE.md                     # This file - project instructions
├── deleted.py                    # Log of deleted code for rollback
├── policies/                     # Policy PDF documents
│   ├── Scootsurance QSR022206_updated.pdf
│   ├── TravelEasy Policy QTD032212.pdf
│   └── TravelEasy Pre-Ex Policy QTD032212-PX.pdf
├── block_one/                    # Block one components
│   ├── test.py                   # Ancileo API testing
│   └── Taxonomy_Hackathon.json   # Source taxonomy structure
├── agents/                       # Agent modules
│   ├── needs_extraction_agent/   # (Empty - future use)
│   ├── policy_intelligence_agent/# (Empty - future use)
│   └── rag_agent/               # RAG pipeline for policy embedding & retrieval
│       ├── __init__.py          # Package exports
│       ├── agent.py             # RAGAgent class - high-level interface
│       ├── tools.py             # PolicyRAGPipeline - embedding & vector store
│       ├── prompt.py            # Prompt templates for policy Q&A
│       ├── retrieval.py         # TaxonomyConditionFiller - fills taxonomy
│       ├── embed_policies.py    # Script 1: Embed all policy PDFs (RUN FIRST)
│       ├── run_retrieval.py     # Script 2: Fill taxonomy conditions (RUN SECOND)
│       ├── test_rag.py          # Test script for RAG pipeline
│       ├── requirements.txt     # Python dependencies
│       ├── README.md            # Usage documentation
│       ├── chroma_db/           # ChromaDB vector store (created by embed_policies.py)
│       └── Taxonomy_Filled.json # Output - filled taxonomy (created by run_retrieval.py)
└── ancileo/                     # Ancileo API integration
```

---

## Pipeline Design

### RAG Embedding & Retrieval Pipeline

**Purpose:** Vectorize policy PDF documents and use them to automatically fill condition information in Taxonomy_Hackathon.json

**Pipeline Flow:**

1. **Embedding Phase** (`tools.py` - PolicyRAGPipeline)
   - Load PDF files from `policies/` using LangChain PyPDFLoader
   - Extract text with metadata (filename, page number)
   - Chunk documents using RecursiveCharacterTextSplitter (1000 chars, 200 overlap)
   - Generate embeddings using OpenAI text-embedding-3-small
   - Store in ChromaDB vector store at `rag_agent/chroma_db/`

2. **Retrieval Phase** (`retrieval.py` - TaxonomyConditionFiller)
   - Load source taxonomy from `block_one/Taxonomy_Hackathon.json`
   - Map products (A, B, C) to policy files
   - For each condition in each layer:
     a. Generate search query based on condition name/type
     b. Retrieve top-k relevant chunks from specific policy using RAG
     c. Use Ollama (gpt-oss:20b) to extract structured information:
        - condition_exist (boolean)
        - original_text (exact policy text)
        - parameters (extracted values)
     d. Update taxonomy with extracted info
   - Save filled taxonomy to `rag_agent/Taxonomy_Filled.json`

3. **Orchestration** (Two separate scripts)

   **a. Embedding Script** (`embed_policies.py`)
   - Standalone script to embed all policy PDFs
   - Creates ChromaDB vector store
   - Run FIRST before taxonomy filling

   **b. Taxonomy Filling Script** (`run_retrieval.py`)
   - Requires ChromaDB to exist (from embed_policies.py)
   - Initialize TaxonomyConditionFiller
   - Options: fill all layers, specific layer, specific conditions, or test mode
   - Progress saved after each layer

**Key Technologies:**
- LangChain: Document loading, chunking, retrieval
- ChromaDB: Vector database for persistent storage
- OpenAI Embeddings: text-embedding-3-small for semantic search
- Google Gemini 2.5 Flash: Cloud LLM for structured extraction from policy text with JSON mode
- Python-dotenv: Environment management
- ThreadPoolExecutor: Parallel processing for batch requests (5 concurrent workers)

**Agent Interface** (`agent.py` - RAGAgent):
- `embed_policies()`: Run embedding pipeline
- `query_policies()`: Semantic search across all policies
- `search_in_policy()`: Search within specific policy
- `get_policy_context()`: Format context for LLM prompts

---

## Latest Changes (2025-11-01)

### RAG Agent - Final Version

**Major Updates:**

1. **Switched from Ollama to Gemini API** (retrieval.py)
   - Replaced local Ollama with Google Gemini 2.5 Flash
   - Enabled JSON mode (`response_mime_type: "application/json"`) for guaranteed structured output
   - More capable model with better extraction accuracy
   - No local dependencies required

2. **Enhanced Prompt Engineering** (retrieval.py:145-211)
   - Strict schema enforcement with detailed field requirements
   - Clear extraction rules (no inference, explicit only)
   - Example outputs for clarity
   - Structured sections: TASK → CONTEXT → SCHEMA → RULES → FORMAT → EXAMPLES

3. **Resumable Pipeline with Overwrite Control** (retrieval.py:28-51, 313-344)
   - Added `overwrite` flag (default: False)
   - Automatically skips already-filled layers
   - `_is_layer_filled()` method detects existing data
   - Progress saved after each layer for crash recovery
   - Force re-fill with `overwrite=True`

4. **Verbose Debug Mode** (retrieval.py:33-47, 281-319, run_retrieval.py:48-67)
   - Added `verbose` flag for detailed debugging
   - Shows: RAG queries, retrieved context, Gemini responses, parsing results
   - Helps diagnose "not found" conditions
   - Optional mode to reduce noise during normal runs

5. **Batch Processing for Speed** (retrieval.py:13, 35, 397-471)
   - Parallel processing using ThreadPoolExecutor
   - Process multiple products concurrently (default: 5 workers)
   - Significantly faster than sequential processing
   - Thread-safe Gemini API calls

6. **Improved Output Display** (retrieval.py:418-463)
   - Shows extracted policy text (first 150 chars)
   - Displays parameters or "(none extracted)"
   - Clear status indicators: ✓ Found / ✗ Not found
   - Hints to enable verbose mode for debugging

7. **Intelligent Semantic Extraction** (retrieval.py:151-262)
   - Completely rewritten prompt to be SMART and FLEXIBLE
   - Encourages semantic matching (e.g., "good_health" → "pre-existing conditions")
   - Understands insurance terminology and concepts
   - Maps different policy wordings to standard conditions
   - Provides semantic matching examples in prompt
   - Much fewer false "not found" results

**Components:**
- embed_policies.py: Standalone embedding process (run first)
- run_retrieval.py: Taxonomy filling process with interactive prompts
- test_first_10.py: NEW - Test script for first 10 conditions (saves to test_output.json)
- retrieval.py: Core TaxonomyConditionFiller with Gemini extraction
- requirements.txt: Updated with google-generativeai>=0.3.0

**Testing:**
```bash
# Quick test on first 10 conditions
python test_first_10.py

# Full pipeline
python run_retrieval.py
```
