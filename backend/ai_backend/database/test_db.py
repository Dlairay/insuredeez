"""
Test script for User Profile Database
Demonstrates CRUD operations
"""

import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))

from database.user_profile import UserProfileDB
from database.db_manager import DatabaseManager


def main():
    """Test database operations"""
    print("="*70)
    print("USER PROFILE DATABASE - TEST SCRIPT")
    print("="*70)

    # Initialize database
    db = UserProfileDB()

    # Test 1: Create user profiles
    print("\n[TEST 1] Creating user profiles...")

    profile1_id = db.create_profile(
        user_id="user_001",
        itinerary="Trip to Japan for 2 weeks - skiing in Hokkaido, visiting Tokyo",
        coverage_needs=[
            {
                "need_category": "layer_2_benefits",
                "taxonomy_tags": ["adventurous_activities", "overseas_medical_expenses"],
                "reasoning": "Skiing activity requires adventure coverage",
                "priority": "HIGH",
                "itinerary_evidence": "skiing in Hokkaido"
            },
            {
                "need_category": "layer_2_benefits",
                "taxonomy_tags": ["trip_cancellation", "trip_curtailment"],
                "reasoning": "Expensive trip needs cancellation protection",
                "priority": "HIGH",
                "itinerary_evidence": "2 weeks trip"
            }
        ],
        trip_summary={
            "destinations": ["Japan", "Hokkaido", "Tokyo"],
            "duration_days": 14,
            "activities": ["skiing", "sightseeing"]
        },
        metadata={"extraction_method": "hybrid"}
    )

    profile2_id = db.create_profile(
        user_id="user_002",
        itinerary="Solo backpacking Thailand - scuba diving in Koh Tao",
        coverage_needs=[
            {
                "need_category": "layer_1_general_conditions",
                "taxonomy_tags": ["underwater_activities_exclusion"],
                "reasoning": "Scuba diving activity",
                "priority": "HIGH",
                "itinerary_evidence": "scuba diving in Koh Tao"
            }
        ],
        trip_summary={
            "destinations": ["Thailand", "Koh Tao"],
            "duration_days": 7,
            "activities": ["scuba diving", "backpacking"]
        }
    )

    print(f"✓ Created profile 1 (doc_id: {profile1_id})")
    print(f"✓ Created profile 2 (doc_id: {profile2_id})")

    # Test 2: Retrieve profiles
    print("\n[TEST 2] Retrieving profiles...")

    user1_profile = db.get_profile_by_user_id("user_001")
    print(f"\n  User 001 Profile:")
    print(f"    - Coverage needs: {len(user1_profile['coverage_needs'])}")
    print(f"    - Trip duration: {user1_profile['trip_summary']['duration_days']} days")
    print(f"    - Created: {user1_profile['created_at']}")

    # Test 3: Update profile
    print("\n[TEST 3] Updating profile...")

    new_need = {
        "need_category": "layer_2_benefits",
        "taxonomy_tags": ["personal_belongings"],
        "reasoning": "Carrying expensive camera equipment",
        "priority": "MEDIUM",
        "itinerary_evidence": "N/A"
    }

    db.add_coverage_need(profile1_id, new_need)
    updated_profile = db.get_profile_by_doc_id(profile1_id)
    print(f"✓ Added new coverage need. Total needs: {len(updated_profile['coverage_needs'])}")

    # Test 4: Search by tags
    print("\n[TEST 4] Searching by taxonomy tags...")

    profiles_with_medical = db.search_by_tags(["overseas_medical_expenses"])
    print(f"  Profiles with 'overseas_medical_expenses': {len(profiles_with_medical)}")

    profiles_with_scuba = db.search_by_tags(["underwater_activities_exclusion"])
    print(f"  Profiles with 'underwater_activities_exclusion': {len(profiles_with_scuba)}")

    # Test 5: Search by priority
    print("\n[TEST 5] Searching by priority...")

    high_priority_profiles = db.search_by_priority("HIGH")
    print(f"  Profiles with HIGH priority needs: {len(high_priority_profiles)}")

    # Test 6: Database statistics
    print("\n[TEST 6] Database statistics...")

    stats = db.get_stats()
    print(f"\n  Database Stats:")
    print(f"    - Total profiles: {stats['total_profiles']}")
    print(f"    - Total coverage needs: {stats['total_coverage_needs']}")
    print(f"    - Unique taxonomy tags: {stats['unique_taxonomy_tags']}")
    print(f"    - Priority distribution: {stats['priority_distribution']}")
    print(f"    - Avg needs per profile: {stats['avg_needs_per_profile']:.2f}")

    # Test 7: Database manager stats
    print("\n[TEST 7] Database manager stats...")

    db_manager = DatabaseManager()
    db_stats = db_manager.get_stats()
    print(f"\n  Database Info:")
    print(f"    - Path: {db_stats['db_path']}")
    print(f"    - Tables: {list(db_stats['tables'].keys())}")
    print(f"    - Total documents: {db_stats['total_documents']}")

    print("\n" + "="*70)
    print("ALL TESTS COMPLETED!")
    print("="*70)

    # Show database file location
    print(f"\nDatabase file created at:")
    print(f"  {db_manager.db_path}")
    print(f"\nYou can inspect it - it's a human-readable JSON file!")


if __name__ == "__main__":
    main()
