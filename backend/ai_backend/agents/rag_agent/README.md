# RAG Agent - Policy Embedding & Taxonomy Filling
#### DO NOT MODIFY THIS FOLDER IT IS ALREADY PEFRECT I"LL FUCKING UNSUBSCRIBE IF U TOUCH THIS
Automated pipeline for vectorizing policy documents and filling taxonomy conditions using RAG + Gemini.

## Quick Start

### 1. Install Dependencies

```bash
cd /Users/ray/Desktop/hackdeez/backend/ai_backend/agents/rag_agent
pip install -r requirements.txt
```

### 2. Step 1: Embed Policy Documents (Run First)

```bash
python embed_policies.py
```

This will:
- Load all PDF files from `policies/` directory
- Extract text and chunk documents
- Generate OpenAI embeddings
- Create ChromaDB vector store at `chroma_db/`

**Output:** ChromaDB created at `rag_agent/chroma_db/`

### 3. Step 2: Fill Taxonomy Conditions (Run Second)

```bash
python run_retrieval.py
```

This will:
- Load the embedded policies from ChromaDB
- Initialize the taxonomy filler
- Prompt you to choose what to fill:
  - Option 1: Fill all layers (full pipeline)
  - Option 2: Fill specific layer
  - Option 3: Fill specific conditions
  - Option 4: Test mode (fills first 3 conditions)

**Output:** Filled taxonomy saved to `rag_agent/Taxonomy_Filled.json`

## Usage Examples

### Programmatic Usage

```python
from agents.rag_agent import RAGAgent, TaxonomyConditionFiller

# Embed policies
agent = RAGAgent()
agent.embed_policies()

# Fill taxonomy
filler = TaxonomyConditionFiller(
    taxonomy_path="/path/to/Taxonomy_Hackathon.json"
)
filler.fill_all_layers()
```

### Query Policies

```python
from agents.rag_agent import create_rag_agent

agent = create_rag_agent(auto_load=True)

# Search all policies
results = agent.query_policies("What is the age limit?", k=3)

# Search specific policy
results = agent.search_in_policy(
    "TravelEasy Policy QTD032212.pdf",
    "pre-existing conditions",
    k=5
)

# Get formatted context for LLM
context = agent.get_policy_context("coverage limits", context_size=3)
```

## Pipeline Architecture

```
┌─────────────────────────────────────────────────────────────┐
│       STEP 1: EMBEDDING PHASE (embed_policies.py)          │
├─────────────────────────────────────────────────────────────┤
│  policies/ (PDFs)                                           │
│       ↓                                                     │
│  PyPDFLoader → RecursiveTextSplitter                        │
│       ↓                                                     │
│  OpenAI Embeddings (text-embedding-3-small)                 │
│       ↓                                                     │
│  ChromaDB (rag_agent/chroma_db/)  ← RUN THIS FIRST          │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│    STEP 2: RETRIEVAL PHASE (run_retrieval.py)              │
├─────────────────────────────────────────────────────────────┤
│  ChromaDB + Taxonomy_Hackathon.json                         │
│       ↓                                                     │
│  For each condition:                                        │
│    ├─ Generate query from condition name                   │
│    ├─ RAG retrieval (top-k chunks from policy)             │
│    ├─ Ollama extraction (condition_exist, text, params)    │
│    └─ Update taxonomy                                       │
│       ↓                                                     │
│  Taxonomy_Filled.json  ← RUN THIS SECOND                    │
└─────────────────────────────────────────────────────────────┘
```

## Files

**Core Modules:**
- `agent.py` - RAGAgent class with high-level interface
- `tools.py` - PolicyRAGPipeline for embedding & vector store
- `prompt.py` - Prompt templates for policy Q&A
- `retrieval.py` - TaxonomyConditionFiller for taxonomy filling

**Executable Scripts:**
- `embed_policies.py` - **Step 1:** Embed policy PDFs (run first)
- `run_retrieval.py` - **Step 2:** Fill taxonomy conditions (run second)
- `test_rag.py` - Test script for RAG queries

## Environment Variables

Required in `.env`:
```
OPENAI_API_KEY=your_openai_key
```

**Note:** Ollama must be installed and running locally with the `gpt-oss:20b` model.

Install Ollama: https://ollama.ai/
Pull model: `ollama pull gpt-oss:20b`

## Customization

### Modify Policy-Product Mapping

Edit `retrieval.py` line ~47:

```python
def _create_policy_mapping(self) -> Dict[str, str]:
    return {
        "Product A": "Scootsurance QSR022206_updated.pdf",
        "Product B": "TravelEasy Policy QTD032212.pdf",
        "Product C": "TravelEasy Pre-Ex Policy QTD032212-PX.pdf"
    }
```

### Adjust Chunking Parameters

Edit `tools.py` line ~30:

```python
chunk_size=1000,      # Change chunk size
chunk_overlap=200,    # Change overlap
```

### Change Retrieval Count

Edit `retrieval.py` line ~159:

```python
k=5  # Number of chunks to retrieve per query
```
