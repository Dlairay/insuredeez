"""
Tools for Plan Selector Agent
Selects the best insurance plan (A, B, or C) based on needs and coverage
"""

from typing import Dict
import json
import os

# Path to Taxonomy_Filled.json (READ ONLY)
TAXONOMY_PATH = "/Users/ray/Desktop/hackdeez/backend/ai_backend/agents/rag_agent/Taxonomy_Filled.json"

def select_best_plan(needs_data: Dict, coverage_data: Dict, profile_artifact: Dict) -> Dict:
    """
    Select the best insurance plan (Product A, B, or C) based on user needs and coverage requirements

    Args:
        needs_data: Dictionary of identified needs from needs_agent
        coverage_data: Recommended coverage amounts from coverage_agent
        profile_artifact: User profile with trip details

    Returns:
        Dictionary with selected plan, score breakdown, and justification
    """

    # Load Taxonomy_Filled.json for plan comparison (READ ONLY)
    try:
        with open(TAXONOMY_PATH, 'r') as f:
            taxonomy = json.load(f)
    except Exception as e:
        return {
            "error": f"Failed to load taxonomy: {str(e)}",
            "selected_plan": None
        }

    identified_needs = needs_data.get("identified_needs", [])
    recommended_coverage = coverage_data.get("recommended_coverage", {})

    # Score each product based on how well it matches the user's needs
    scores = {
        "Product A": 0,
        "Product B": 0,
        "Product C": 0
    }

    # Simplified scoring logic (in production, would analyze full taxonomy)
    # For now, use a simple heuristic based on trip complexity

    needs_count = len(identified_needs)
    has_adventure = any("adventurous" in need for need in identified_needs)
    has_cruise = any("cruise" in need for need in identified_needs)
    medical_coverage_needed = recommended_coverage.get("medical_expenses", 0)

    # Product A: Basic coverage
    if needs_count < 10 and medical_coverage_needed < 20000:
        scores["Product A"] = 100

    # Product B: Standard coverage
    if 5 < needs_count < 15 and 10000 < medical_coverage_needed < 50000:
        scores["Product B"] = 100
    elif not has_adventure and not has_cruise:
        scores["Product B"] = 80

    # Product C: Comprehensive coverage (Pre-Ex)
    if needs_count > 10 or has_adventure or has_cruise or medical_coverage_needed > 30000:
        scores["Product C"] = 100
    elif needs_count > 8:
        scores["Product C"] = 70

    # Adjust scores based on number of travelers
    travelers = profile_artifact.get("adultsCount", 1) + profile_artifact.get("childrenCount", 0)
    if travelers > 2:
        scores["Product C"] += 20  # Families benefit from comprehensive coverage

    # Select the plan with highest score
    selected_plan = max(scores, key=scores.get)

    # Build justification
    justification_points = []
    if has_adventure:
        justification_points.append("Adventure activities require comprehensive coverage")
    if has_cruise:
        justification_points.append("Cruise travel benefits from specialized coverage")
    if medical_coverage_needed > 30000:
        justification_points.append("High medical coverage needs identified")
    if travelers > 2:
        justification_points.append("Family travel requires broader protection")
    if needs_count > 10:
        justification_points.append("Multiple coverage needs identified")

    return {
        "selected_plan": selected_plan,
        "scores": scores,
        "confidence": scores[selected_plan],
        "justification": justification_points,
        "needs_matched": needs_count,
        "recommended_medical_coverage": medical_coverage_needed
    }
