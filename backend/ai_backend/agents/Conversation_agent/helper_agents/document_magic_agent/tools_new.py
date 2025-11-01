"""
NEW SIMPLIFIED TOOLS - No base64 parameter, agent extracts directly
"""

import os
import sys
from typing import Dict, List

sys.path.append('/Users/ray/Desktop/hackdeez/backend/ai_backend')
from profile_manager import load_profile, save_profile


def save_document_data(extracted_data: str, doc_type: str = "auto") -> Dict:
    """
    Save extracted document data to user profile

    The agent itself extracts data using vision, this tool just saves it.

    Args:
        extracted_data: JSON string with extracted fields
        doc_type: Type of document ("passport", "itinerary", "auto")

    Returns:
        Dictionary with success status and missing fields
    """
    import json

    user_id = os.environ.get('CURRENT_USER_ID', 'default_user')
    print(f"[DEBUG] save_document_data called for user: {user_id}")
    print(f"[DEBUG] extracted_data: {extracted_data[:200]}...")

    # Load profile
    profile = load_profile(user_id)

    # Parse extracted data
    try:
        data = json.loads(extracted_data)
        print(f"[DEBUG] Parsed data: {data}")
    except Exception as e:
        print(f"[ERROR] Failed to parse JSON: {e}")
        return {
            "success": False,
            "error": f"Invalid JSON: {str(e)}"
        }

    # Update profile with extracted data
    updates_made = []

    # Trip fields
    for field in ['tripType', 'departureDate', 'returnDate', 'departureCountry', 'arrivalCountry', 'adultsCount', 'childrenCount']:
        if field in data:
            profile[field] = data[field]
            updates_made.append(field)

    # Ensure insureds array exists
    if not profile.get('insureds'):
        profile['insureds'] = [{}]

    insured = profile['insureds'][0]

    # Personal fields for first insured
    for field in ['title', 'firstName', 'lastName', 'nationality', 'dateOfBirth', 'passport', 'email', 'phoneNumber', 'phoneType']:
        if field in data:
            insured[field] = data[field]
            updates_made.append(f"insureds.0.{field}")

    # Set defaults
    if not insured.get('id'):
        insured['id'] = '1'
    if not insured.get('relationship'):
        insured['relationship'] = 'main'

    profile['insureds'][0] = insured

    # Copy to mainContact (same person)
    for field in ['title', 'firstName', 'lastName', 'nationality', 'dateOfBirth', 'passport', 'email', 'phoneNumber', 'phoneType']:
        if field in data:
            profile['mainContact'][field] = data[field]

    if not profile['mainContact'].get('id'):
        profile['mainContact']['id'] = '1'

    # Save profile
    save_profile(user_id, profile)

    # Identify missing fields
    missing = _identify_missing(profile)

    # Check if we now have minimum fields for policy recommendations
    has_destination = bool(profile.get('arrivalCountry'))
    has_date = bool(profile.get('departureDate') or profile.get('returnDate'))
    ready_for_policy_recs = has_destination and has_date

    print(f"[DEBUG] Updates made: {updates_made}")
    print(f"[DEBUG] Missing fields: {missing}")
    print(f"[DEBUG] Ready for policy recs: {ready_for_policy_recs} (destination={has_destination}, date={has_date})")

    return {
        "success": True,
        "updates_made": updates_made,
        "missing_fields": missing,
        "ready_for_policy_recommendations": ready_for_policy_recs,
        "destination": profile.get('arrivalCountry', ''),
        "departure_date": profile.get('departureDate', ''),
        "message": f"Saved {len(updates_made)} fields. {len(missing)} still missing. {'READY FOR POLICY RECS!' if ready_for_policy_recs else 'Need destination + date for policy recs.'}"
    }


def _identify_missing(profile: Dict) -> List[str]:
    """Identify missing required fields"""
    missing = []

    # Trip info
    if not profile.get('tripType'):
        missing.append('tripType')
    if not profile.get('departureDate'):
        missing.append('departureDate')
    if not profile.get('returnDate'):
        missing.append('returnDate')
    if not profile.get('departureCountry'):
        missing.append('departureCountry')
    if not profile.get('arrivalCountry'):
        missing.append('arrivalCountry')
    if not profile.get('adultsCount'):
        missing.append('adultsCount')

    # Personal info
    insureds = profile.get('insureds', [])
    if insureds:
        insured = insureds[0]
        for field in ['title', 'firstName', 'lastName', 'nationality', 'dateOfBirth', 'passport', 'email', 'phoneNumber']:
            if not insured.get(field):
                missing.append(field)

    # Contact info
    contact = profile.get('mainContact', {})
    for field in ['email', 'phoneNumber', 'address', 'city', 'zipCode', 'countryCode']:
        if not contact.get(field):
            missing.append(f"contact.{field}")

    return missing
