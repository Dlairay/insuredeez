"""
Tools for Policy Recommendation Agent
All three tools: analyze needs (2-stage Gemini + DB), recommend coverage (real DB), select plan (taxonomy matching)
"""

import os
import sys
import json
from typing import Dict
from google import genai

# Import profile manager and DB helper
sys.path.append('/Users/ray/Desktop/hackdeez/backend/ai_backend')
from profile_manager import load_profile, save_profile
from db_helper import get_claim_stats

# Paths
TAXONOMY_PATH = "/Users/ray/Desktop/hackdeez/backend/ai_backend/agents/rag_agent/taxonomy_data.json"


# ============================================================================
# TOOL 1: Analyze Itinerary Needs (Two-Stage Gemini + DB)
# ============================================================================

def analyze_itinerary_needs(itinerary_text: str) -> Dict:
    """
    TWO-STAGE ANALYSIS: Analyze travel itinerary to identify insurance needs

    STAGE 1: Extract destination + initial risk assessment
    STAGE 2: Refine needs based on REAL historical claims data from DB

    Args:
        itinerary_text: Text describing the travel itinerary

    Returns:
        Dictionary with updated needs and list of identified needs
    """
    user_id = os.environ.get('CURRENT_USER_ID', 'default_user')
    print(f"[DEBUG] analyze_itinerary_needs called for user: {user_id}")

    profile = load_profile(user_id)
    current_needs = profile.get("needs", {})
    needs_list = list(current_needs.keys())

    print(f"[DEBUG] TWO-STAGE ANALYSIS starting...")

    try:
        client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

        # STAGE 1: Extract destination + initial needs
        print(f"[STAGE 1] Extracting destination and initial risk assessment...")

        stage1_prompt = f"""Analyze this travel itinerary.

**Travel Itinerary:**
{itinerary_text}

**Available Insurance Needs:**
{json.dumps(needs_list, indent=2)}

**Return JSON:**
{{
  "destination": "Country Name",
  "initial_needs": ["need1", "need2", ...]
}}"""

        response1 = client.models.generate_content(
            model='gemini-2.0-flash-exp',
            contents=stage1_prompt
        )

        response1_text = response1.text.strip()
        if "```json" in response1_text:
            response1_text = response1_text.split("```json")[1].split("```")[0].strip()
        elif "```" in response1_text:
            response1_text = response1_text.split("```")[1].split("```")[0].strip()

        stage1_result = json.loads(response1_text)
        destination = stage1_result.get("destination", "")
        initial_needs = stage1_result.get("initial_needs", [])

        print(f"[STAGE 1] Destination: {destination}, Initial needs: {len(initial_needs)}")

        # QUERY DATABASE
        print(f"[DB QUERY] Fetching real claims data for {destination}...")
        db_stats = get_claim_stats(destination)

        if db_stats:
            print(f"[DB QUERY] Claim type: {db_stats['claim_type']}, Avg: ${db_stats['gross_incurred']:,.2f}")
            profile["arrivalCountry"] = destination
        else:
            print(f"[DB QUERY] No data for {destination}")
            db_stats = {"destination": destination, "claim_type": "Unknown", "cause_of_loss": "Unknown", "gross_incurred": 0.0}

        # STAGE 2: Refine with DB data
        print(f"[STAGE 2] Refining needs with real claims data...")

        stage2_prompt = f"""REFINE insurance needs based on REAL claims data.

**Initial:** {json.dumps(initial_needs)}
**REAL DATA for {destination}:**
- Claim type: {db_stats['claim_type']}
- Cause: {db_stats['cause_of_loss']}
- Avg: ${db_stats['gross_incurred']:,.2f}

**Available Needs:** {json.dumps(needs_list, indent=2)}

Add needs based on claims data. Always include basic travel needs.
Return JSON array: ["need1", "need2", ...]"""

        response2 = client.models.generate_content(
            model='gemini-2.0-flash-exp',
            contents=stage2_prompt
        )

        response2_text = response2.text.strip()
        if "```json" in response2_text:
            response2_text = response2_text.split("```json")[1].split("```")[0].strip()
        elif "```" in response2_text:
            response2_text = response2_text.split("```")[1].split("```")[0].strip()

        refined_needs = json.loads(response2_text)
        print(f"[STAGE 2] Refined: {len(refined_needs)} needs")

        # Update profile
        updated_needs = current_needs.copy()
        for need in refined_needs:
            if need in updated_needs:
                updated_needs[need] = True

        profile["needs"] = updated_needs
        save_profile(user_id, profile)

        return {
            "success": True,
            "user_id": user_id,
            "destination": destination,
            "identified_needs": refined_needs,
            "needs_count": len([v for v in updated_needs.values() if v]),
            "db_stats": db_stats,
            "message": f"Two-stage analysis: {len(refined_needs)} needs for {destination}"
        }

    except Exception as e:
        print(f"[ERROR] {e}")
        return {
            "success": False,
            "error": str(e),
            "user_id": user_id,
            "identified_needs": [],
            "needs_count": 0
        }


# ============================================================================
# TOOL 2: Recommend Coverage (Real DB Data)
# ============================================================================

def recommend_coverage() -> Dict:
    """
    Recommend coverage amounts using REAL historical claims data from PostgreSQL

    Returns:
        Dictionary with recommended coverage amounts based on real data
    """
    user_id = os.environ.get('CURRENT_USER_ID', 'default_user')
    print(f"[DEBUG] recommend_coverage called for user: {user_id}")

    profile = load_profile(user_id)
    needs = profile.get("needs", {})
    trip_type = profile.get("tripType", "ST")
    adults = profile.get("adultsCount", 1)
    children = profile.get("childrenCount", 0)
    total_travelers = adults + children if (adults + children) > 0 else 1
    destination = profile.get("arrivalCountry", "")

    # Query REAL database
    db_stats = get_claim_stats(destination)

    if db_stats:
        avg_claim = db_stats['gross_incurred']
        claim_type = db_stats['claim_type']

        print(f"[DEBUG] Using REAL data: ${avg_claim:,.2f}, type: {claim_type}")

        buffer = 1.2
        medical_mult = 1.5 if "medical" in claim_type.lower() else 1.0

        recommended_coverage = {
            "medical_expenses": int(avg_claim * buffer * medical_mult * total_travelers),
            "emergency_evacuation": int(avg_claim * 0.5 * buffer),
            "personal_effects": int(avg_claim * 0.3 * buffer * total_travelers),
            "trip_cancellation": int(avg_claim * buffer),
            "category": f"real_data_{destination}",
            "justification": f"Real claims for {destination}: ${avg_claim:,.2f}, {claim_type}",
            "data_source": "PostgreSQL"
        }
    else:
        # Fallback
        print(f"[WARNING] No DB data, using estimates")
        has_adventure = needs.get("adventurous_activities", False)
        has_cruise = needs.get("cruise_cover", False)

        base = 50000 if has_adventure else (20000 if has_cruise else 15000)

        recommended_coverage = {
            "medical_expenses": int(base * 1.2 * total_travelers),
            "emergency_evacuation": int(base * 0.5 * 1.2),
            "personal_effects": int(3000 * 1.2 * total_travelers),
            "trip_cancellation": int(50000 * 1.2),
            "category": "estimates",
            "justification": f"Estimates (no data for {destination})",
            "data_source": "fallback"
        }

    if trip_type == "AN":
        recommended_coverage["medical_expenses"] = int(recommended_coverage["medical_expenses"] * 1.5)

    return {
        "success": True,
        "recommended_coverage": recommended_coverage,
        "claims_analysis": {"destination": destination, "travelers": total_travelers, "db_stats": db_stats}
    }


# ============================================================================
# TOOL 3: Select Best Plan (Taxonomy Matching)
# ============================================================================

def select_best_plan() -> Dict:
    """
    Select best insurance plan using REAL taxonomy matching from taxonomy_data.json

    Returns:
        Dictionary with selected plan and match analysis
    """
    user_id = os.environ.get('CURRENT_USER_ID', 'default_user')
    print(f"[DEBUG] select_best_plan called for user: {user_id}")

    profile = load_profile(user_id)
    needs = profile.get("needs", {})
    identified_needs = [k for k, v in needs.items() if v]

    print(f"[DEBUG] Matching {len(identified_needs)} needs against taxonomy")

    # Load taxonomy
    try:
        with open(TAXONOMY_PATH, 'r') as f:
            taxonomy = json.load(f)
    except Exception as e:
        return {"success": False, "error": str(e)}

    # Match needs against products
    coverage_match = {
        "Product A": {"matched": 0, "matched_needs": []},
        "Product B": {"matched": 0, "matched_needs": []},
        "Product C": {"matched": 0, "matched_needs": []}
    }

    for layer_key, conditions in taxonomy.get("layers", {}).items():
        for condition_item in conditions:
            condition_name = condition_item.get("condition") or condition_item.get("benefit_name", "")

            if condition_name in identified_needs:
                products_data = condition_item.get("products", {})

                for product_name in ["Product A", "Product B", "Product C"]:
                    if product_name in products_data:
                        product_info = products_data[product_name]
                        if product_info.get("condition_exist") or product_info.get("benefit_exist"):
                            coverage_match[product_name]["matched"] += 1
                            coverage_match[product_name]["matched_needs"].append(condition_name)

    # Calculate scores
    scores = {}
    for product in ["Product A", "Product B", "Product C"]:
        matched = coverage_match[product]["matched"]
        total = len(identified_needs)
        scores[product] = int((matched / total) * 100) if total > 0 else 0

    # Determine recommended plan (highest score)
    recommended_plan = max(scores, key=scores.get)

    # Get coverage recommendations from profile
    coverage_rec = {}
    try:
        # Try to get coverage data if recommend_coverage was called
        coverage_rec = {
            "medical_expenses": profile.get("recommended_medical", 0),
            "emergency_evacuation": profile.get("recommended_evacuation", 0),
            "personal_effects": profile.get("recommended_effects", 0)
        }
    except:
        pass

    # Build product cards for all 3 plans
    products = {
        "Product A": {
            "name": "Product A",
            "match_percentage": scores["Product A"],
            "needs_matched": coverage_match["Product A"]["matched"],
            "total_needs": len(identified_needs),
            "matched_needs": coverage_match["Product A"]["matched_needs"],
            "is_recommended": recommended_plan == "Product A",
            "coverage": coverage_rec
        },
        "Product B": {
            "name": "Product B",
            "match_percentage": scores["Product B"],
            "needs_matched": coverage_match["Product B"]["matched"],
            "total_needs": len(identified_needs),
            "matched_needs": coverage_match["Product B"]["matched_needs"],
            "is_recommended": recommended_plan == "Product B",
            "coverage": coverage_rec
        },
        "Product C": {
            "name": "Product C",
            "match_percentage": scores["Product C"],
            "needs_matched": coverage_match["Product C"]["matched"],
            "total_needs": len(identified_needs),
            "matched_needs": coverage_match["Product C"]["matched_needs"],
            "is_recommended": recommended_plan == "Product C",
            "coverage": coverage_rec
        }
    }

    return {
        "success": True,
        "products": products,
        "recommended": recommended_plan,
        "summary": {
            "total_needs_identified": len(identified_needs),
            "destination": profile.get("arrivalCountry", "Unknown")
        }
    }
