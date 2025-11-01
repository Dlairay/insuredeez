"""
Tools for Coverage Recommendation Agent
Analyzes claims history to suggest coverage amounts
"""

from typing import Dict
import os
import json

# Mock claims database (in production, this would query the PDF or actual database)
CLAIMS_DB = {
    "adventure_trips": {
        "average_medical_claim": 50000,
        "average_evacuation_claim": 25000,
        "average_equipment_claim": 3000
    },
    "standard_trips": {
        "average_medical_claim": 15000,
        "average_evacuation_claim": 10000,
        "average_equipment_claim": 1000
    },
    "cruise_trips": {
        "average_medical_claim": 20000,
        "average_evacuation_claim": 15000,
        "average_equipment_claim": 2000
    },
    "family_trips": {
        "average_medical_claim": 30000,
        "average_evacuation_claim": 18000,
        "average_equipment_claim": 1500
    }
}

def recommend_coverage(profile_artifact: Dict) -> Dict:
    """
    Recommend coverage amounts based on trip profile and historical claims data

    Args:
        profile_artifact: User profile with trip details and needs

    Returns:
        Dictionary with recommended coverage amounts and justification
    """

    needs = profile_artifact.get("needs", {})
    trip_type = profile_artifact.get("tripType", "ST")
    adults = profile_artifact.get("adultsCount", 1)
    children = profile_artifact.get("childrenCount", 0)
    total_travelers = adults + children

    # Determine trip category based on needs
    has_adventure = needs.get("adventurous_activities", False)
    has_cruise = needs.get("cruise_cover", False)
    is_family = children > 0

    if has_adventure:
        category = "adventure_trips"
    elif has_cruise:
        category = "cruise_trips"
    elif is_family:
        category = "family_trips"
    else:
        category = "standard_trips"

    # Get base claims data
    claims_data = CLAIMS_DB.get(category, CLAIMS_DB["standard_trips"])

    # Calculate recommended coverage (add 20% buffer)
    buffer_multiplier = 1.2
    recommended_coverage = {
        "medical_expenses": int(claims_data["average_medical_claim"] * buffer_multiplier * total_travelers),
        "emergency_evacuation": int(claims_data["average_evacuation_claim"] * buffer_multiplier),
        "personal_effects": int(claims_data["average_equipment_claim"] * buffer_multiplier * total_travelers),
        "trip_cancellation": int(50000 * buffer_multiplier),  # Standard recommendation
        "category": category,
        "justification": f"Based on {category.replace('_', ' ')} historical claims data"
    }

    # Adjust for annual vs single trip
    if trip_type == "AN":
        recommended_coverage["medical_expenses"] = int(recommended_coverage["medical_expenses"] * 1.5)
        recommended_coverage["justification"] += " (increased for annual coverage)"

    return {
        "recommended_coverage": recommended_coverage,
        "claims_analysis": {
            "trip_category": category,
            "historical_avg_medical": claims_data["average_medical_claim"],
            "historical_avg_evacuation": claims_data["average_evacuation_claim"],
            "travelers_count": total_travelers
        }
    }
