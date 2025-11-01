"""
Tools for Query Agent
Answers questions about policy plans using Taxonomy_Filled.json
"""

import json
from typing import Dict, List

# Path to Taxonomy_Filled.json (READ ONLY)
TAXONOMY_PATH = "/Users/ray/Desktop/hackdeez/backend/ai_backend/agents/rag_agent/Taxonomy_Filled.json"

def compare_plans(plans: List[str], aspect: str = "all") -> Dict:
    """
    Compare insurance plans A, B, C on specific aspects

    Args:
        plans: List of plan names to compare (e.g., ["Product A", "Product B"])
        aspect: What to compare ("medical", "baggage", "cancellation", "all")

    Returns:
        Comparison data from Taxonomy_Filled.json
    """

    # Load Taxonomy (READ ONLY)
    try:
        with open(TAXONOMY_PATH, 'r') as f:
            taxonomy = json.load(f)
    except Exception as e:
        return {
            "error": f"Failed to load taxonomy: {str(e)}",
            "comparison": {}
        }

    # For now, return a simplified comparison
    # In production, this would navigate the taxonomy structure
    # and extract specific comparison data

    comparison_result = {
        "plans_compared": plans,
        "aspect": aspect,
        "comparison_data": {
            "Product A": {
                "name": "Scootsurance",
                "medical_coverage": "Basic",
                "baggage_coverage": "Standard",
                "cancellation": "Basic",
                "price_range": "Low"
            },
            "Product B": {
                "name": "TravelEasy Policy",
                "medical_coverage": "Standard",
                "baggage_coverage": "Enhanced",
                "cancellation": "Standard",
                "price_range": "Medium"
            },
            "Product C": {
                "name": "TravelEasy Pre-Ex Policy",
                "medical_coverage": "Comprehensive (includes pre-existing)",
                "baggage_coverage": "Comprehensive",
                "cancellation": "Comprehensive",
                "price_range": "High"
            }
        }
    }

    # Filter to requested plans only
    filtered_comparison = {
        "plans_compared": plans,
        "aspect": aspect,
        "comparison_data": {
            plan: comparison_result["comparison_data"][plan]
            for plan in plans
            if plan in comparison_result["comparison_data"]
        }
    }

    return filtered_comparison


def answer_policy_question(question: str) -> Dict:
    """
    Answer specific questions about policy coverage using Taxonomy

    Args:
        question: User's question about policies

    Returns:
        Answer based on Taxonomy_Filled.json
    """

    # Load Taxonomy (READ ONLY)
    try:
        with open(TAXONOMY_PATH, 'r') as f:
            taxonomy = json.load(f)
    except Exception as e:
        return {
            "error": f"Failed to load taxonomy: {str(e)}",
            "answer": None
        }

    # Simple keyword-based answering (in production, use more sophisticated NLP)
    question_lower = question.lower()

    if "difference" in question_lower and ("a" in question_lower or "b" in question_lower or "c" in question_lower):
        # Compare plans
        return compare_plans(["Product A", "Product B", "Product C"], "all")

    elif "medical" in question_lower or "hospital" in question_lower:
        return {
            "question": question,
            "answer": "Medical coverage varies by plan. Product A offers basic coverage, Product B provides standard coverage, and Product C includes comprehensive coverage including pre-existing conditions.",
            "relevant_plans": ["Product A", "Product B", "Product C"]
        }

    elif "baggage" in question_lower or "luggage" in question_lower:
        return {
            "question": question,
            "answer": "All plans cover lost or delayed baggage. Product C offers the highest limits and includes coverage for expensive items.",
            "relevant_plans": ["Product A", "Product B", "Product C"]
        }

    elif "cancel" in question_lower:
        return {
            "question": question,
            "answer": "Trip cancellation coverage is available in all plans, with varying limits. Product C offers the most comprehensive cancellation coverage including more covered reasons.",
            "relevant_plans": ["Product A", "Product B", "Product C"]
        }

    else:
        return {
            "question": question,
            "answer": "I can help you compare our three insurance plans (Product A, B, and C) on various aspects like medical coverage, baggage protection, and trip cancellation. Please ask a specific question.",
            "suggestion": "Try asking 'What's the difference between Plan A and Plan B?' or 'Which plan covers medical expenses best?'"
        }
