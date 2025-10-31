"""
Tools for Needs Extraction Agent
Handles taxonomy loading, itinerary parsing, and database operations
"""

import sys
from pathlib import Path
from typing import Dict, List, Optional

# Add parent directory to path for imports
parent_dir = str(Path(__file__).parent.parent.parent)
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

from block_one.taxonomy_conditions_data import result as taxonomy_data
from database.user_profile import UserProfileDB


class TaxonomyLoader:
    """Loads and provides access to taxonomy condition tags"""

    def __init__(self):
        self.taxonomy = taxonomy_data

    def get_layer_1_conditions(self) -> list:
        """Get all Layer 1 general condition tags"""
        return self.taxonomy.get('layer_1_general_conditions', [])

    def get_layer_2_benefits(self) -> list:
        """Get all Layer 2 benefit tags"""
        return self.taxonomy.get('layer_2_benefits', [])

    def get_layer_3_conditions(self) -> list:
        """Get all Layer 3 benefit-specific condition tags"""
        return self.taxonomy.get('layer_3_benefit_specific_conditions', [])

    def get_all_tags(self) -> dict:
        """Get all taxonomy tags organized by layer"""
        return {
            'layer_1': self.get_layer_1_conditions(),
            'layer_2': self.get_layer_2_benefits(),
            'layer_3': self.get_layer_3_conditions()
        }

    def validate_tags(self, tags: list) -> tuple:
        """
        Validate if provided tags exist in taxonomy

        Returns:
            (valid_tags, invalid_tags)
        """
        all_valid_tags = set(
            self.get_layer_1_conditions() +
            self.get_layer_2_benefits() +
            self.get_layer_3_conditions()
        )

        valid = [tag for tag in tags if tag in all_valid_tags]
        invalid = [tag for tag in tags if tag not in all_valid_tags]

        return valid, invalid

    def search_tags(self, keyword: str) -> dict:
        """
        Search for tags containing keyword

        Returns:
            Dictionary with matching tags per layer
        """
        keyword_lower = keyword.lower()

        return {
            'layer_1': [tag for tag in self.get_layer_1_conditions() if keyword_lower in tag.lower()],
            'layer_2': [tag for tag in self.get_layer_2_benefits() if keyword_lower in tag.lower()],
            'layer_3': [tag for tag in self.get_layer_3_conditions() if keyword_lower in tag.lower()]
        }


class ItineraryParser:
    """Helper functions for parsing itinerary text"""

    @staticmethod
    def extract_activities_keywords() -> dict:
        """
        Keywords that map to specific coverage needs

        Returns dict of {keyword: [related_taxonomy_tags]}
        """
        return {
            # Adventure activities
            'ski': ['high_altitude_exclusion', 'adventurous_activities', 'accidental_death_permanent_disablement'],
            'scuba': ['underwater_activities_exclusion', 'adventurous_activities', 'overseas_medical_expenses'],
            'dive': ['underwater_activities_exclusion', 'adventurous_activities'],
            'mountain': ['mountaineering_exclusion', 'high_altitude_exclusion', 'adventurous_activities'],
            'hiking': ['adventurous_activities', 'accidental_death_permanent_disablement'],
            'bungee': ['dangerous_activities_exclusion', 'adventurous_activities'],
            'skydive': ['aerial_activity_exclusion', 'dangerous_activities_exclusion'],
            'paraglid': ['aerial_activity_exclusion', 'dangerous_activities_exclusion'],

            # Medical
            'elderly': ['age_eligibility', 'overseas_medical_expenses', 'medical_expenses_in_singapore'],
            'pregnant': ['pregnancy_related_conditions', 'maternity_overseas_medical_expenses'],
            'medical condition': ['pre_existing_conditions', 'overseas_medical_expenses'],
            'medication': ['vaccination_and_medication_requirement', 'overseas_medical_expenses'],

            # Family
            'child': ['child_accompaniment_requirement', 'child_guard', 'child_education_grant'],
            'kids': ['child_accompaniment_requirement', 'child_guard'],
            'family': ['child_accompaniment_requirement'],

            # Expensive items
            'camera': ['loss_damage_personal_belongings', 'personal_money'],
            'laptop': ['loss_damage_personal_belongings'],
            'jewelry': ['loss_damage_personal_belongings'],
            'wedding': ['loss_damage_wedding_clothing'],
            'golf': ['golfer', 'loss_or_damage_of_golfing_equipment'],

            # Trip disruption
            'expensive': ['trip_cancellation', 'trip_curtailment', 'travel_delay'],
            'non-refundable': ['trip_cancellation', 'trip_curtailment'],
            'cruise': ['trip_cancellation', 'trip_curtailment', 'overseas_medical_expenses'],

            # Transportation
            'rental car': ['rental_vehicle_excess', 'returning_rental_vehicle'],
            'driving': ['rental_vehicle_excess'],

            # Destinations
            'remote': ['emergency_medical_evacuation_repatriation', 'medical_travel_assistance'],
            'jungle': ['adventurous_activities', 'emergency_medical_evacuation_repatriation'],
            'safari': ['adventurous_activities', 'dangerous_activities_exclusion'],
        }

    @staticmethod
    def detect_risk_factors(itinerary_text: str) -> list:
        """
        Detect risk factors from itinerary text

        Returns list of detected risk keywords
        """
        itinerary_lower = itinerary_text.lower()
        keywords = ItineraryParser.extract_activities_keywords()

        detected = []
        for keyword in keywords.keys():
            if keyword in itinerary_lower:
                detected.append(keyword)

        return detected


# ============================================================================
# DATABASE TOOLS - Agent invokes these to interact with user profile database
# ============================================================================

def save_coverage_profile(
    user_id: str,
    itinerary: str,
    coverage_needs: List[Dict],
    trip_summary: Dict,
    metadata: Optional[Dict] = None
) -> Dict:
    """
    Tool: Save extracted coverage needs profile to database

    Args:
        user_id: Unique user identifier
        itinerary: Original itinerary text
        coverage_needs: List of extracted coverage needs with taxonomy tags
        trip_summary: Trip summary information
        metadata: Optional extraction metadata

    Returns:
        Dictionary with save result and profile info
    """
    try:
        db = UserProfileDB()
        doc_id = db.create_profile(
            user_id=user_id,
            itinerary=itinerary,
            coverage_needs=coverage_needs,
            trip_summary=trip_summary,
            metadata=metadata
        )

        return {
            "success": True,
            "doc_id": doc_id,
            "user_id": user_id,
            "total_needs": len(coverage_needs),
            "message": f"Profile saved with doc_id {doc_id}"
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "message": f"Failed to save profile: {str(e)}"
        }


def get_user_profile(user_id: str) -> Dict:
    """
    Tool: Retrieve user's most recent coverage needs profile

    Args:
        user_id: User identifier

    Returns:
        User profile dictionary or error
    """
    try:
        db = UserProfileDB()
        profile = db.get_profile_by_user_id(user_id)

        if profile:
            return {
                "success": True,
                "profile": profile,
                "message": f"Found profile for user {user_id}"
            }
        else:
            return {
                "success": False,
                "message": f"No profile found for user {user_id}"
            }
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "message": f"Error retrieving profile: {str(e)}"
        }


def search_profiles_by_tags(tags: List[str]) -> Dict:
    """
    Tool: Search for profiles containing specific taxonomy tags

    Args:
        tags: List of taxonomy tags to search for

    Returns:
        Dictionary with matching profiles
    """
    try:
        db = UserProfileDB()
        profiles = db.search_by_tags(tags)

        return {
            "success": True,
            "profiles": profiles,
            "count": len(profiles),
            "tags_searched": tags,
            "message": f"Found {len(profiles)} profile(s) matching tags"
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "message": f"Error searching profiles: {str(e)}"
        }


def update_coverage_needs(
    user_id: str,
    additional_needs: List[Dict],
    replace: bool = False
) -> Dict:
    """
    Tool: Update user's coverage needs (add or replace)

    Args:
        user_id: User identifier
        additional_needs: New coverage needs to add
        replace: If True, replace all needs; if False, append

    Returns:
        Dictionary with update result
    """
    try:
        db = UserProfileDB()
        profile = db.get_profile_by_user_id(user_id)

        if not profile:
            return {
                "success": False,
                "message": f"No profile found for user {user_id}"
            }

        doc_id = profile.doc_id

        if replace:
            # Replace all coverage needs
            success = db.update_profile(doc_id, coverage_needs=additional_needs)
            action = "replaced"
        else:
            # Append new needs
            for need in additional_needs:
                db.add_coverage_need(doc_id, need)
            success = True
            action = "added"

        if success:
            return {
                "success": True,
                "doc_id": doc_id,
                "needs_count": len(additional_needs),
                "action": action,
                "message": f"Successfully {action} {len(additional_needs)} coverage need(s)"
            }
        else:
            return {
                "success": False,
                "message": "Update operation failed"
            }

    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "message": f"Error updating profile: {str(e)}"
        }


def get_database_stats() -> Dict:
    """
    Tool: Get statistics about the user profile database

    Returns:
        Dictionary with database statistics
    """
    try:
        db = UserProfileDB()
        stats = db.get_stats()

        return {
            "success": True,
            "stats": stats,
            "message": "Database statistics retrieved"
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "message": f"Error getting stats: {str(e)}"
        }
