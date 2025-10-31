"""
Test script for RAG pipeline
Demonstrates embedding policy documents and querying them
"""

import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent.parent.parent))

from agents.rag_agent import RAGAgent, create_rag_agent


def test_embed_policies():
    """Test embedding all policy documents"""
    print("\n" + "=" * 70)
    print("TEST 1: Embedding Policy Documents")
    print("=" * 70)

    # Create RAG agent
    agent = RAGAgent()

    # Embed policies
    success = agent.embed_policies()

    if success:
        print("\n✓ Successfully embedded all policy documents!")
    else:
        print("\n✗ Failed to embed policy documents")
        return False

    return True


def test_query_policies():
    """Test querying policy documents"""
    print("\n" + "=" * 70)
    print("TEST 2: Querying Policy Documents")
    print("=" * 70)

    # Create agent with auto-load
    agent = create_rag_agent(auto_load=True)

    # Test queries
    test_queries = [
        "What is covered under travel insurance?",
        "What are the pre-existing conditions exclusions?",
        "What is the coverage limit for medical expenses?",
        "What countries are covered by this policy?"
    ]

    for i, query in enumerate(test_queries, 1):
        print(f"\n--- Query {i}: {query} ---")

        try:
            results = agent.query_policies(query, k=2)

            for j, result in enumerate(results, 1):
                print(f"\nResult {j}:")
                print(f"  Source: {result['filename']}, Page {result['page']}")
                print(f"  Content: {result['content'][:200]}...")

        except Exception as e:
            print(f"Error querying: {e}")
            return False

    print("\n✓ Successfully queried policy documents!")
    return True


def test_query_with_scores():
    """Test querying with similarity scores"""
    print("\n" + "=" * 70)
    print("TEST 3: Query with Similarity Scores")
    print("=" * 70)

    agent = create_rag_agent(auto_load=True)

    query = "What are the coverage limits?"
    print(f"\nQuery: {query}")

    try:
        results = agent.query_policies(query, k=3, include_scores=True)

        for i, result in enumerate(results, 1):
            print(f"\nResult {i}:")
            print(f"  Source: {result['filename']}, Page {result['page']}")
            print(f"  Score: {result['similarity_score']:.4f}")
            print(f"  Content: {result['content'][:150]}...")

        print("\n✓ Successfully queried with scores!")
        return True

    except Exception as e:
        print(f"Error: {e}")
        return False


def test_search_specific_policy():
    """Test searching within a specific policy"""
    print("\n" + "=" * 70)
    print("TEST 4: Search Specific Policy")
    print("=" * 70)

    agent = create_rag_agent(auto_load=True)

    # Get available policies
    policies = agent.get_available_policies()
    print(f"\nAvailable policies: {policies}")

    if policies:
        policy_name = policies[0]
        query = "coverage limits"

        print(f"\nSearching in: {policy_name}")
        print(f"Query: {query}")

        try:
            results = agent.search_in_policy(policy_name, query, k=2)

            for i, result in enumerate(results, 1):
                print(f"\nResult {i}:")
                print(f"  Page {result['page']}")
                print(f"  Content: {result['content'][:200]}...")

            print("\n✓ Successfully searched specific policy!")
            return True

        except Exception as e:
            print(f"Error: {e}")
            return False

    return False


def test_get_context():
    """Test getting formatted context for LLM"""
    print("\n" + "=" * 70)
    print("TEST 5: Get Formatted Context")
    print("=" * 70)

    agent = create_rag_agent(auto_load=True)

    query = "What is covered for trip cancellation?"
    print(f"\nQuery: {query}")

    try:
        context = agent.get_policy_context(query, context_size=2)
        print(f"\nFormatted Context:\n{context}")

        print("\n✓ Successfully retrieved formatted context!")
        return True

    except Exception as e:
        print(f"Error: {e}")
        return False


def run_all_tests():
    """Run all tests"""
    print("\n" + "=" * 70)
    print("RAG PIPELINE TEST SUITE")
    print("=" * 70)

    # Test 1: Embedding (run first time only)
    # Uncomment the line below on first run to embed documents
    # test_embed_policies()

    # Test 2-5: Querying (requires embedded documents)
    tests = [
        test_query_policies,
        test_query_with_scores,
        test_search_specific_policy,
        test_get_context
    ]

    results = []
    for test_func in tests:
        try:
            result = test_func()
            results.append(result)
        except Exception as e:
            print(f"\n✗ Test failed with exception: {e}")
            results.append(False)

    # Summary
    print("\n" + "=" * 70)
    print("TEST SUMMARY")
    print("=" * 70)
    passed = sum(results)
    total = len(results)
    print(f"Passed: {passed}/{total}")

    if passed == total:
        print("\n✓ All tests passed!")
    else:
        print(f"\n✗ {total - passed} test(s) failed")


if __name__ == "__main__":
    # For first run: embed the policies
    print("Do you want to embed policies first? (y/n): ", end="")
    response = input().strip().lower()

    if response == 'y':
        test_embed_policies()
        print("\nPolicies embedded! Now run this script again to test queries.")
    else:
        # Run query tests
        run_all_tests()
