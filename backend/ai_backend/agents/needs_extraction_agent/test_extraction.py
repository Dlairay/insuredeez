"""
Test script for Needs Extraction Agent
Demonstrates extraction from sample itineraries
"""

import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent.parent))

from agents.needs_extraction_agent.agent import NeedsExtractionAgent
import json


# Sample itinerary 1: Adventure trip
SAMPLE_ITINERARY_1 = """
Trip to Swiss Alps - Family Ski Vacation

Dates: December 15-28, 2024 (14 days)

Travelers:
- Me (45 years old)
- Wife (42 years old)
- Two kids (ages 8 and 12)

Itinerary:
Day 1-2: Flight from Singapore to Zurich, transfer to Zermatt
- Non-refundable business class tickets ($12,000 total)
- Booked 5-star hotel in Zermatt ($8,000 for entire stay)

Day 3-10: Skiing in Zermatt
- Kids will take ski lessons
- Planning to ski on Matterhorn glacier (altitude 3,800m)
- Rented ski equipment and winter gear

Day 11-12: Day trip to Jungfraujoch (Top of Europe - 3,454m altitude)
- Scenic train ride
- Ice palace visit

Day 13: Last day skiing, evening flight back to Zurich
Day 14: Morning flight back to Singapore

Special Notes:
- This is an expensive trip with non-refundable deposits
- Bringing expensive camera equipment ($5,000 worth)
- My wife has a history of altitude sickness
- Kids traveling with us the entire trip
"""

SAMPLE_ITINERARY_2 = """
Solo backpacking trip to Thailand and Vietnam

Duration: 3 weeks in February 2025

About me: 28 year old, healthy, adventurous traveler

Plans:
Week 1 - Thailand:
- Bangkok: Street food tours, temples
- Koh Tao: Scuba diving certification course (will be diving to 18m depth)
- Staying in budget hostels

Week 2 - Northern Thailand:
- Chiang Mai: Cooking classes, elephant sanctuary
- Pai: Renting a motorcycle to explore the area

Week 3 - Vietnam:
- Hanoi: Food tours
- Ha Long Bay: 2-day cruise
- Ho Chi Minh City: Museums and nightlife

Budget: $3,000 total (mostly already paid for flights and some accommodations)

Notes:
- Traveling with just a backpack
- No expensive items besides my laptop ($1,500)
- Very flexible itinerary, may extend if I like a place
- Planning some adventure activities like rock climbing in Railay Beach
"""

SAMPLE_ITINERARY_3 = """
Luxury cruise for elderly parents - 70th birthday celebration

Dates: March 2025, 2 weeks

Travelers:
- Dad (70 years old, has high blood pressure - taking medication daily)
- Mom (68 years old, diabetic - insulin dependent)
- Me and my husband (as companions)

Cruise Details:
- Mediterranean cruise: Barcelona → Rome → Athens → Istanbul → Venice
- Luxury cruise line, premium suite booked ($15,000 per couple)
- All-inclusive package with shore excursions

Special Considerations:
- Dad needs regular medical checkups (has medication for high blood pressure)
- Mom is diabetic and needs insulin refrigeration
- This is a once-in-a-lifetime trip for them
- Shore excursions include walking tours (worried about dad's mobility)
- Booked 3 months in advance, all non-refundable

Medical:
- Both parents are generally healthy but have pre-existing conditions
- Concerned about medical emergencies at sea
- Want comprehensive medical coverage
"""


def main():
    """Run test extractions"""
    print("\n" + "="*70)
    print("NEEDS EXTRACTION AGENT - TEST SCRIPT")
    print("="*70)

    # Initialize agent
    agent = NeedsExtractionAgent()

    # Test samples
    samples = [
        ("Adventure Family Ski Trip", SAMPLE_ITINERARY_1),
        ("Solo Backpacking Adventure", SAMPLE_ITINERARY_2),
        ("Luxury Cruise for Elderly Parents", SAMPLE_ITINERARY_3)
    ]

    for title, itinerary in samples:
        print(f"\n{'='*70}")
        print(f"TEST: {title}")
        print(f"{'='*70}")

        # Extract needs with hybrid approach
        result = agent.extract_needs_with_keyword_boost(itinerary, verbose=True)

        # Print formatted report
        print("\n" + agent.format_needs_report(result))

        # Save raw JSON
        output_file = f"needs_extraction_{title.replace(' ', '_').lower()}.json"
        with open(output_file, 'w') as f:
            json.dump(result, f, indent=2)
        print(f"\n✓ Saved raw JSON to: {output_file}")

        print("\n" + "="*70)
        input("\nPress Enter to continue to next test...")


if __name__ == "__main__":
    main()
