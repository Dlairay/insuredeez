# Needs Extraction Agent

Extracts insurance coverage needs from human-written travel itineraries using taxonomy-grounded tagging.

## Purpose

Automatically analyzes a traveler's itinerary and identifies relevant insurance coverage needs by:
1. Parsing itinerary for destinations, activities, traveler profile, risks
2. Mapping identified needs to standardized taxonomy tags
3. Prioritizing needs (HIGH/MEDIUM/LOW) based on risk assessment
4. Providing reasoning and evidence for each identified need

## Files

- `agent.py` - Main NeedsExtractionAgent class
- `tools.py` - TaxonomyLoader and ItineraryParser utilities
- `prompt.py` - Prompts for LLM-based extraction
- `test_extraction.py` - Test script with sample itineraries

## Usage

```python
from agents.needs_extraction_agent.agent import NeedsExtractionAgent

# Initialize agent
agent = NeedsExtractionAgent()

# Extract needs from itinerary
itinerary = """
Trip to Japan for 2 weeks
- Tokyo, Kyoto, Osaka
- Skiing in Hokkaido
- Traveling with elderly parents (70+ years old)
- Non-refundable flights and hotels ($10,000 total)
"""

result = agent.extract_needs_with_keyword_boost(itinerary, verbose=True)

# Print formatted report
print(agent.format_needs_report(result))
```

## Output Format

```json
{
  "coverage_needs": [
    {
      "need_category": "layer_2_benefits",
      "taxonomy_tags": ["trip_cancellation", "trip_curtailment"],
      "reasoning": "Expensive non-refundable bookings require trip cancellation protection",
      "priority": "HIGH",
      "itinerary_evidence": "Non-refundable flights and hotels ($10,000 total)"
    }
  ],
  "trip_summary": {
    "destinations": ["Tokyo", "Kyoto", "Osaka", "Hokkaido"],
    "duration_days": 14,
    "activities": ["skiing", "sightseeing"],
    "risk_factors": ["high_altitude", "elderly_travelers", "expensive_trip"]
  },
  "_metadata": {
    "total_tags": 15,
    "valid_tags": 15,
    "invalid_tags": 0,
    "model_used": "gemini-2.0-flash-exp"
  }
}
```

## Features

### 1. Taxonomy-Grounded Tagging
Uses `block_one/taxonomy_conditions_data.py` to ensure all extracted needs map to valid taxonomy terms across 3 layers:
- Layer 1: General conditions (age eligibility, exclusions, etc.)
- Layer 2: Benefits (medical coverage, trip cancellation, etc.)
- Layer 3: Benefit-specific conditions (time limits, requirements, etc.)

### 2. Hybrid Extraction
- **LLM-based**: Gemini analyzes full itinerary context for intelligent extraction
- **Keyword-based**: Pattern matching for high-recall detection of activities/risks
- Merges both approaches to maximize coverage

### 3. Intelligent Mapping
Automatically detects risks from itinerary:
- "scuba diving" → `underwater_activities_exclusion`, `adventurous_activities`
- "elderly parent" → `age_eligibility`, `medical_expenses`
- "non-refundable" → `trip_cancellation`, `trip_curtailment`
- "rental car" → `rental_vehicle_excess`

### 4. Priority Assessment
Categorizes needs by risk severity:
- **HIGH**: Critical coverage (medical, expensive trip cancellation)
- **MEDIUM**: Important but not critical (baggage, delays)
- **LOW**: Nice-to-have (entertainment tickets, domestic pets)

## Test Script

Run the test script to see sample extractions:

```bash
cd /Users/ray/Desktop/hackdeez/backend/ai_backend/agents/needs_extraction_agent
python test_extraction.py
```

Tests 3 sample itineraries:
1. Family ski trip (adventure + altitude + kids)
2. Solo backpacking (budget + adventure + flexibility)
3. Luxury cruise for elderly parents (pre-existing conditions + expensive)

## Integration

This agent outputs a coverage needs profile that can be used to:
1. Auto-fill user coverage preferences
2. Match against policy product offerings
3. Generate personalized insurance recommendations
4. Highlight gaps in current coverage

The rest of the needs (not extracted from itinerary) will be filled via a separate process to be designed later.
