"""
Tools for Needs Agent
Analyzes itinerary to identify insurance needs
"""

from typing import Dict, List

def analyze_itinerary_needs(itinerary_text: str, profile_artifact: Dict) -> Dict:
    """
    Analyze travel itinerary to identify which insurance needs should be set to True

    Args:
        itinerary_text: Text describing the travel itinerary
        profile_artifact: User profile with needs taxonomy

    Returns:
        Dictionary with updated needs and list of identified needs
    """

    updated_needs = profile_artifact.get("needs", {}).copy()
    identified_needs = []

    # Convert itinerary to lowercase for easier matching
    itinerary_lower = itinerary_text.lower()

    # Activity-based needs
    if any(word in itinerary_lower for word in ["ski", "skiing", "snowboard", "snow"]):
        updated_needs["adventurous_activities"] = True
        updated_needs["sports_equipment"] = True
        identified_needs.append("adventurous_activities")
        identified_needs.append("sports_equipment")

    if any(word in itinerary_lower for word in ["scuba", "dive", "diving", "snorkel"]):
        updated_needs["adventurous_activities"] = True
        updated_needs["water_sports"] = True
        identified_needs.append("adventurous_activities")
        identified_needs.append("water_sports")

    if any(word in itinerary_lower for word in ["hike", "hiking", "trek", "mountain", "climb"]):
        updated_needs["adventurous_activities"] = True
        identified_needs.append("adventurous_activities")

    if any(word in itinerary_lower for word in ["cruise", "ship"]):
        updated_needs["cruise_cover"] = True
        identified_needs.append("cruise_cover")

    if any(word in itinerary_lower for word in ["rental car", "hire car", "car rental"]):
        updated_needs["car_hire_excess"] = True
        updated_needs["accidental_loss_or_damage_to_rental_vehicle"] = True
        identified_needs.append("car_hire_excess")

    # Medical and emergency needs (always recommended for international travel)
    if profile_artifact.get("arrivalCountry") and profile_artifact.get("arrivalCountry") != profile_artifact.get("departureCountry"):
        updated_needs["24hours_emergency_medical_assistance"] = True
        updated_needs["24hours_travel_assistance"] = True
        updated_needs["emergency_medical_expenses"] = True
        updated_needs["emergency_medical_evacuation"] = True
        identified_needs.extend([
            "24hours_emergency_medical_assistance",
            "24hours_travel_assistance",
            "emergency_medical_expenses",
            "emergency_medical_evacuation"
        ])

    # Travel disruption needs (common for all trips)
    updated_needs["baggage_and_personal_effects"] = True
    updated_needs["baggage_delay"] = True
    updated_needs["travel_delay"] = True
    updated_needs["trip_cancellation_or_curtailment"] = True
    identified_needs.extend([
        "baggage_and_personal_effects",
        "baggage_delay",
        "travel_delay",
        "trip_cancellation_or_curtailment"
    ])

    # COVID-19 coverage (recommended for all travelers)
    updated_needs["covid_19_travel_inconvenience"] = True
    identified_needs.append("covid_19_travel_inconvenience")

    # Update profile
    updated_profile = profile_artifact.copy()
    updated_profile["needs"] = updated_needs

    return {
        "updated_profile": updated_profile,
        "identified_needs": list(set(identified_needs)),  # Remove duplicates
        "needs_count": len([v for v in updated_needs.values() if v])
    }
