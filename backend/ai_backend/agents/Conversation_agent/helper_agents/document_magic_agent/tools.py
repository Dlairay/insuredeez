"""
Tools for Document Magic Agent
Extracts information from documents using Gemini Vision API
"""

import base64
import re
from typing import Dict, List
from datetime import datetime
from google import genai
import os

# Configure Gemini API
client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

def extract_and_fill_profile(base64_image: str, profile_artifact: Dict, doc_type: str = "auto") -> Dict:
    """
    Extract information from base64-encoded document image and fill profile artifact

    Args:
        base64_image: Base64 encoded image string
        profile_artifact: The user profile dictionary from schema_template
        doc_type: Type of document ("passport", "itinerary", "auto")

    Returns:
        Dictionary with extracted_data, updated_profile, and missing_fields
    """

    # Remove data:image prefix if present
    if "base64," in base64_image:
        base64_image = base64_image.split("base64,")[1]

    # Decode base64 to bytes
    try:
        image_bytes = base64.b64decode(base64_image)
    except Exception as e:
        return {
            "error": f"Failed to decode image: {str(e)}",
            "extracted_data": {},
            "updated_profile": profile_artifact,
            "missing_fields": []
        }

    # Use Gemini Vision for extraction
    # Using the new google-genai client

    # Create appropriate prompt based on doc_type
    if doc_type == "passport" or doc_type == "auto":
        prompt = """Extract the following information from this passport/ID document:
        - First Name
        - Last Name
        - Nationality (2-letter country code if possible, e.g., SG, US, UK)
        - Date of Birth (format as YYYY-MM-DD)
        - Passport Number
        - Gender/Title (Mr/Mrs/Ms)

        Return the information in JSON format with keys:
        firstName, lastName, nationality, dateOfBirth, passport, title

        If you cannot extract certain fields, omit them from the JSON."""

    else:  # itinerary
        prompt = """Extract the following travel information from this itinerary/booking document:
        - Trip Type (single trip "ST" or annual "AN")
        - Departure Date (format as YYYY-MM-DD)
        - Return Date (format as YYYY-MM-DD)
        - Departure Country (2-letter code, e.g., SG)
        - Arrival/Destination Country (2-letter code)
        - Number of Adults
        - Number of Children
        - Email address (if present)
        - Phone number (if present)

        Return the information in JSON format with keys:
        tripType, departureDate, returnDate, departureCountry, arrivalCountry,
        adultsCount, childrenCount, email, phoneNumber

        If you cannot extract certain fields, omit them from the JSON."""

    try:
        # Call Gemini Vision API using new client
        response = client.models.generate_content(
            model='gemini-2.0-flash-exp',
            contents=[prompt, {"mime_type": "image/jpeg", "data": image_bytes}]
        )
        extracted_text = response.text

        # Parse the JSON response
        import json
        # Extract JSON from response (handle markdown code blocks)
        if "```json" in extracted_text:
            json_str = extracted_text.split("```json")[1].split("```")[0].strip()
        elif "```" in extracted_text:
            json_str = extracted_text.split("```")[1].split("```")[0].strip()
        else:
            json_str = extracted_text.strip()

        extracted_data = json.loads(json_str)

    except Exception as e:
        return {
            "error": f"Extraction failed: {str(e)}",
            "extracted_data": {},
            "updated_profile": profile_artifact,
            "missing_fields": []
        }

    # Update profile artifact with extracted data
    updated_profile = profile_artifact.copy()

    # Map extracted data to profile fields
    if "firstName" in extracted_data:
        # Update insureds if exists
        if updated_profile.get("insureds") and len(updated_profile["insureds"]) > 0:
            updated_profile["insureds"][0]["firstName"] = extracted_data["firstName"]
        # Also update mainContact
        if updated_profile.get("mainContact"):
            updated_profile["mainContact"]["firstName"] = extracted_data["firstName"]

    if "lastName" in extracted_data:
        if updated_profile.get("insureds") and len(updated_profile["insureds"]) > 0:
            updated_profile["insureds"][0]["lastName"] = extracted_data["lastName"]
        if updated_profile.get("mainContact"):
            updated_profile["mainContact"]["lastName"] = extracted_data["lastName"]

    if "nationality" in extracted_data:
        if updated_profile.get("insureds") and len(updated_profile["insureds"]) > 0:
            updated_profile["insureds"][0]["nationality"] = extracted_data["nationality"]
        if updated_profile.get("mainContact"):
            updated_profile["mainContact"]["nationality"] = extracted_data["nationality"]

    if "dateOfBirth" in extracted_data:
        if updated_profile.get("insureds") and len(updated_profile["insureds"]) > 0:
            updated_profile["insureds"][0]["dateOfBirth"] = extracted_data["dateOfBirth"]
        if updated_profile.get("mainContact"):
            updated_profile["mainContact"]["dateOfBirth"] = extracted_data["dateOfBirth"]

    if "passport" in extracted_data:
        if updated_profile.get("insureds") and len(updated_profile["insureds"]) > 0:
            updated_profile["insureds"][0]["passport"] = extracted_data["passport"]
        if updated_profile.get("mainContact"):
            updated_profile["mainContact"]["passport"] = extracted_data["passport"]

    if "title" in extracted_data:
        if updated_profile.get("insureds") and len(updated_profile["insureds"]) > 0:
            updated_profile["insureds"][0]["title"] = extracted_data["title"]
        if updated_profile.get("mainContact"):
            updated_profile["mainContact"]["title"] = extracted_data["title"]

    # Trip-related fields
    if "tripType" in extracted_data:
        updated_profile["tripType"] = extracted_data["tripType"]
    if "departureDate" in extracted_data:
        updated_profile["departureDate"] = extracted_data["departureDate"]
    if "returnDate" in extracted_data:
        updated_profile["returnDate"] = extracted_data["returnDate"]
    if "departureCountry" in extracted_data:
        updated_profile["departureCountry"] = extracted_data["departureCountry"]
    if "arrivalCountry" in extracted_data:
        updated_profile["arrivalCountry"] = extracted_data["arrivalCountry"]
    if "adultsCount" in extracted_data:
        updated_profile["adultsCount"] = extracted_data["adultsCount"]
    if "childrenCount" in extracted_data:
        updated_profile["childrenCount"] = extracted_data["childrenCount"]

    # Contact fields
    if "email" in extracted_data:
        if updated_profile.get("insureds") and len(updated_profile["insureds"]) > 0:
            updated_profile["insureds"][0]["email"] = extracted_data["email"]
        if updated_profile.get("mainContact"):
            updated_profile["mainContact"]["email"] = extracted_data["email"]

    if "phoneNumber" in extracted_data:
        if updated_profile.get("insureds") and len(updated_profile["insureds"]) > 0:
            updated_profile["insureds"][0]["phoneNumber"] = extracted_data["phoneNumber"]
        if updated_profile.get("mainContact"):
            updated_profile["mainContact"]["phoneNumber"] = extracted_data["phoneNumber"]

    # Identify missing required fields
    missing_fields = _get_missing_fields(updated_profile)

    return {
        "extracted_data": extracted_data,
        "updated_profile": updated_profile,
        "missing_fields": missing_fields,
        "success": True
    }


def _get_missing_fields(profile: Dict) -> List[str]:
    """
    Identify which required fields are still missing from the profile

    Args:
        profile: The user profile dictionary

    Returns:
        List of missing field names
    """
    missing = []

    # Check trip fields
    if not profile.get("tripType"):
        missing.append("tripType")
    if not profile.get("departureDate"):
        missing.append("departureDate")
    if not profile.get("departureCountry"):
        missing.append("departureCountry")
    if not profile.get("arrivalCountry"):
        missing.append("arrivalCountry")

    # Check insured person fields
    if profile.get("insureds") and len(profile["insureds"]) > 0:
        insured = profile["insureds"][0]
        if not insured.get("firstName"):
            missing.append("firstName")
        if not insured.get("lastName"):
            missing.append("lastName")
        if not insured.get("dateOfBirth"):
            missing.append("dateOfBirth")
        if not insured.get("passport"):
            missing.append("passport")
        if not insured.get("email"):
            missing.append("email")

    # Check main contact fields
    if profile.get("mainContact"):
        contact = profile["mainContact"]
        if not contact.get("address"):
            missing.append("address")
        if not contact.get("city"):
            missing.append("city")
        if not contact.get("zipCode"):
            missing.append("zipCode")
        if not contact.get("countryCode"):
            missing.append("countryCode")

    return missing
