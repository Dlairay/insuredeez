"""
Tools for Policy Recommendation Agent
Consolidates outputs from sub-agents
"""

from typing import Dict

def consolidate_recommendation(needs_result: Dict, coverage_result: Dict, plan_result: Dict) -> Dict:
    """
    Consolidate outputs from the three sub-agents into a final recommendation

    Args:
        needs_result: Output from needs_agent
        coverage_result: Output from coverage_agent
        plan_result: Output from plan_selector_agent

    Returns:
        Consolidated recommendation with all details
    """

    return {
        "recommended_plan": plan_result.get("selected_plan"),
        "confidence_score": plan_result.get("confidence"),
        "justification": plan_result.get("justification", []),
        "coverage_details": {
            "medical_expenses": coverage_result.get("recommended_coverage", {}).get("medical_expenses"),
            "emergency_evacuation": coverage_result.get("recommended_coverage", {}).get("emergency_evacuation"),
            "personal_effects": coverage_result.get("recommended_coverage", {}).get("personal_effects"),
            "trip_cancellation": coverage_result.get("recommended_coverage", {}).get("trip_cancellation")
        },
        "needs_summary": {
            "total_needs_identified": needs_result.get("needs_count"),
            "key_needs": needs_result.get("identified_needs", [])[:5]  # Top 5
        },
        "plan_comparison": plan_result.get("scores", {})
    }
