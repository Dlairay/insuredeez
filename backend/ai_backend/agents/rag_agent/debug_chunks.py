"""Debug script to see what's in the ChromaDB chunks"""

import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent.parent))

from agents.rag_agent.agent import RAGAgent

# Load RAG agent
agent = RAGAgent(auto_load=True)

# Search for age eligibility in Product B
print("Searching for 'age eligibility' in Product B (TravelEasy Pre-Ex)...")
results = agent.search_in_policy(
    "TravelEasy Pre-Ex Policy QTD032212-PX.pdf",
    "age eligibility minimum maximum years old insured person eligibility requirements conditions policy",
    k=10
)

print(f"\nFound {len(results)} chunks:")
print("="*80)

for i, result in enumerate(results, 1):
    print(f"\n[Chunk {i}] Page {result['page']}")
    print(f"Length: {len(result['content'])} characters")
    print(f"Content:\n{result['content']}")
    print("-"*80)
