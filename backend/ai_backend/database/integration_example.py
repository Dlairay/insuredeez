"""
Integration Example: Needs Extraction Agent + User Profile Database

Demonstrates end-to-end flow:
1. Extract coverage needs from itinerary
2. Save to user profile database
3. Retrieve and query profiles
"""

import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))

from agents.needs_extraction_agent.agent import NeedsExtractionAgent
from database.user_profile import UserProfileDB


def extract_and_save(user_id: str, itinerary: str):
    """
    Extract coverage needs from itinerary and save to database

    Args:
        user_id: User identifier
        itinerary: Travel itinerary text

    Returns:
        Document ID of saved profile
    """
    print("="*70)
    print(f"PROCESSING USER: {user_id}")
    print("="*70)

    # Step 1: Extract coverage needs
    print("\n[1] Extracting coverage needs from itinerary...")
    agent = NeedsExtractionAgent()
    result = agent.extract_needs_with_keyword_boost(itinerary, verbose=True)

    # Step 2: Save to database
    print("\n[2] Saving to database...")
    db = UserProfileDB()

    doc_id = db.create_profile(
        user_id=user_id,
        itinerary=itinerary,
        coverage_needs=result.get('coverage_needs', []),
        trip_summary=result.get('trip_summary', {}),
        metadata=result.get('_metadata', {})
    )

    print(f"\n✓ Profile saved with doc_id: {doc_id}")

    # Step 3: Print formatted report
    print("\n[3] Coverage Needs Report:")
    print(agent.format_needs_report(result))

    return doc_id


def main():
    """Run integration example"""
    print("\n" + "="*70)
    print("INTEGRATION EXAMPLE: NEEDS EXTRACTION + DATABASE")
    print("="*70)

    # Example itinerary
    itinerary = """
Family Trip to New Zealand - 3 weeks

Dates: January 10-31, 2025

Travelers:
- Dad (me, 45 years old)
- Mom (42 years old)
- Kids (ages 10 and 14)
- Grandma (70 years old, has diabetes and high blood pressure)

Trip Details:
- Auckland to Queenstown to Christchurch
- Non-refundable flights and hotels: $18,000 total
- Activities planned:
  * Bungee jumping in Queenstown (for me only!)
  * Skiing at Coronet Peak
  * Milford Sound cruise
  * Hiking in Fiordland National Park

Special Considerations:
- Grandma needs regular medication (diabetes + BP meds)
- Expensive camera equipment ($6,000 worth) - I'm a photography enthusiast
- Kids will be skiing for the first time
- Renting a campervan for part of the trip
- Travel insurance is a must given the expensive bookings and activities
    """

    # Extract and save
    doc_id = extract_and_save("user_nz_001", itinerary)

    # Query examples
    print("\n" + "="*70)
    print("QUERYING DATABASE")
    print("="*70)

    db = UserProfileDB()

    # Get profile
    print("\n[QUERY 1] Get profile by user ID:")
    profile = db.get_profile_by_user_id("user_nz_001")
    if profile:
        print(f"  User: {profile['user_id']}")
        print(f"  Coverage needs: {len(profile['coverage_needs'])}")
        print(f"  Destinations: {profile['trip_summary'].get('destinations', [])}")

    # Search by tags
    print("\n[QUERY 2] Search profiles with 'age_eligibility' tag:")
    results = db.search_by_tags(["age_eligibility"])
    print(f"  Found {len(results)} profile(s)")

    # Search by priority
    print("\n[QUERY 3] Search profiles with HIGH priority needs:")
    results = db.search_by_priority("HIGH")
    print(f"  Found {len(results)} profile(s)")
    if results:
        for i, r in enumerate(results, 1):
            high_needs = [n for n in r['coverage_needs'] if n.get('priority') == 'HIGH']
            print(f"    Profile {i}: {len(high_needs)} HIGH priority needs")

    # Database stats
    print("\n[QUERY 4] Database statistics:")
    stats = db.get_stats()
    for key, value in stats.items():
        print(f"  {key}: {value}")

    print("\n" + "="*70)
    print("INTEGRATION COMPLETE!")
    print("="*70)

    print("\nNext steps:")
    print("  1. Use this profile to match against insurance products")
    print("  2. Generate personalized recommendations")
    print("  3. Highlight coverage gaps based on needs")


if __name__ == "__main__":
    main()
