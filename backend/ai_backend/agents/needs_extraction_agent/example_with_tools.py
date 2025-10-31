"""
Example: Using Database Tools with Needs Extraction Agent

Demonstrates how the agent uses tools to interact with the database artifact
"""

import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent.parent))

from agents.needs_extraction_agent.agent import NeedsExtractionAgent
from agents.needs_extraction_agent.tools import (
    save_coverage_profile,
    get_user_profile,
    search_profiles_by_tags,
    update_coverage_needs,
    get_database_stats
)


def main():
    """Demonstrate agent using database tools"""
    print("="*70)
    print("AGENT USING DATABASE TOOLS")
    print("="*70)

    # Sample itinerary
    itinerary = """
    Weekend ski trip to Whistler, Canada
    - 3 days, December 2024
    - Staying at luxury resort ($2,000 non-refundable)
    - Advanced skiing on black diamond runs
    - Traveling with expensive camera gear ($4,000)
    """

    user_id = "user_whistler_001"

    # Step 1: Agent extracts coverage needs
    print("\n[STEP 1] Agent extracts coverage needs from itinerary")
    agent = NeedsExtractionAgent()
    result = agent.extract_needs_with_keyword_boost(itinerary, verbose=False)

    print(f"✓ Extracted {len(result['coverage_needs'])} coverage needs")

    # Step 2: Agent uses TOOL to save to database
    print("\n[STEP 2] Agent invokes save_coverage_profile() tool")
    save_result = save_coverage_profile(
        user_id=user_id,
        itinerary=itinerary,
        coverage_needs=result['coverage_needs'],
        trip_summary=result['trip_summary'],
        metadata=result.get('_metadata')
    )

    print(f"Tool result: {save_result['message']}")
    print(f"  - Success: {save_result['success']}")
    print(f"  - Doc ID: {save_result.get('doc_id')}")
    print(f"  - Total needs: {save_result.get('total_needs')}")

    # Step 3: Agent uses TOOL to retrieve profile
    print("\n[STEP 3] Agent invokes get_user_profile() tool")
    get_result = get_user_profile(user_id)

    if get_result['success']:
        profile = get_result['profile']
        print(f"Tool result: {get_result['message']}")
        print(f"  - User: {profile['user_id']}")
        print(f"  - Destinations: {profile['trip_summary'].get('destinations', [])}")
        print(f"  - Coverage needs: {len(profile['coverage_needs'])}")

    # Step 4: Agent uses TOOL to search by tags
    print("\n[STEP 4] Agent invokes search_profiles_by_tags() tool")
    search_result = search_profiles_by_tags(["adventurous_activities", "trip_cancellation"])

    print(f"Tool result: {search_result['message']}")
    print(f"  - Found: {search_result['count']} profile(s)")
    print(f"  - Tags searched: {search_result['tags_searched']}")

    # Step 5: Agent uses TOOL to add additional need
    print("\n[STEP 5] Agent invokes update_coverage_needs() tool")
    additional_need = [{
        "need_category": "layer_2_benefits",
        "taxonomy_tags": ["rental_vehicle_excess"],
        "reasoning": "User mentioned renting a car",
        "priority": "MEDIUM",
        "itinerary_evidence": "Manually added by agent"
    }]

    update_result = update_coverage_needs(
        user_id=user_id,
        additional_needs=additional_need,
        replace=False  # Append, don't replace
    )

    print(f"Tool result: {update_result['message']}")
    print(f"  - Action: {update_result.get('action')}")
    print(f"  - Needs added: {update_result.get('needs_count')}")

    # Step 6: Agent uses TOOL to get database stats
    print("\n[STEP 6] Agent invokes get_database_stats() tool")
    stats_result = get_database_stats()

    if stats_result['success']:
        stats = stats_result['stats']
        print(f"Tool result: {stats_result['message']}")
        print(f"  - Total profiles: {stats['total_profiles']}")
        print(f"  - Total needs: {stats['total_coverage_needs']}")
        print(f"  - Unique tags: {stats['unique_taxonomy_tags']}")
        print(f"  - Priority distribution: {stats['priority_distribution']}")

    print("\n" + "="*70)
    print("DEMONSTRATION COMPLETE")
    print("="*70)
    print("\nKey Points:")
    print("  • Agent extracts needs using LLM + keywords")
    print("  • Agent invokes TOOLS to interact with database")
    print("  • Database is an ARTIFACT (persistent storage)")
    print("  • Tools provide clean interface for CRUD operations")
    print("  • Follows Google ADK pattern")


if __name__ == "__main__":
    main()
