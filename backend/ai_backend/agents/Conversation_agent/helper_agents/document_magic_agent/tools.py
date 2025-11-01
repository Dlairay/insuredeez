"""
Tools for Document Magic Agent
Extracts information from documents and fills the user schema artifact
Makes API calls for insurance quotes and purchases
"""

import base64
import re
import requests
from typing import Dict, List, Optional
from datetime import datetime
from google import genai
from google.genai.types import Tool, FunctionDeclaration
import os
import json
import copy
import sys

# Import profile manager for file-based storage
sys.path.append('/Users/ray/Desktop/hackdeez/backend/ai_backend')
from profile_manager import load_profile, save_profile


def process_document(base64_image: str, doc_type: str = "auto") -> Dict:
    """
    Process document and update user's persistent profile

    Note: This tool gets user_id from the agent context automatically.
    When called by parent conversation_agent, the user_id is available in session.

    Args:
        base64_image: Base64 encoded document image
        doc_type: Type of document ("passport", "itinerary", "auto")

    Returns:
        Dictionary with updated_schema, missing_fields, and status
    """
    # Try to get user_id from environment variable set by runner
    # This is a workaround for sub-agent tool calls
    user_id = os.environ.get('CURRENT_USER_ID', 'default_user')

    print(f"[DEBUG] process_document called with user_id from context: {user_id}")
    print(f"[DEBUG] base64_image type: {type(base64_image)}, length: {len(base64_image) if hasattr(base64_image, '__len__') else 'N/A'}")

    # Load profile from disk
    user_schema = load_profile(user_id)

    # Process the document - modifies user_schema IN PLACE
    result = extract_and_fill_profile(user_schema, base64_image, doc_type)

    print(f"[DEBUG] extraction result: success={result.get('success')}, error={result.get('error')}")

    # Save updated profile back to disk
    save_profile(user_id, user_schema)

    print(f"[DEBUG] process_document complete, returning result")

    return result


def extract_and_fill_profile(user_schema: Dict, base64_image: str, doc_type: str = "auto") -> Dict:
    """
    Extract information from base64-encoded document image and fill the user schema

    Args:
        user_schema: The user schema artifact to fill (from schema_template.py)
        base64_image: Base64 encoded image string OR raw bytes
        doc_type: Type of document ("passport", "itinerary", "auto")

    Returns:
        Dictionary with updated_schema, missing_fields, and completeness status
    """

    # Handle both base64 string and raw bytes
    if isinstance(base64_image, bytes):
        # Already bytes, use directly
        file_bytes = base64_image
        print(f"[DEBUG] Received raw bytes ({len(file_bytes)} bytes)")
    else:
        # Base64 string, decode it
        # Remove data:image prefix if present
        if "base64," in base64_image:
            base64_image = base64_image.split("base64,")[1]

        # Decode base64 to bytes
        try:
            file_bytes = base64.b64decode(base64_image)
            print(f"[DEBUG] Decoded base64 to bytes ({len(file_bytes)} bytes)")
        except Exception as e:
            print(f"[ERROR] Failed to decode base64: {e}")
            return {
                "error": f"Failed to decode image: {str(e)}",
                "updated_schema": user_schema
            }

    # Detect file type
    mime_type = "image/png"  # default
    if file_bytes.startswith(b'%PDF'):
        mime_type = "application/pdf"
    elif file_bytes.startswith(b'\xff\xd8\xff'):
        mime_type = "image/jpeg"
    elif file_bytes.startswith(b'\x89PNG'):
        mime_type = "image/png"

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
        # Initialize Gemini client
        client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

        print(f"[DEBUG] Calling Gemini Vision API with {mime_type}...")

        # Call Gemini Vision API
        from google.genai.types import Part
        response = client.models.generate_content(
            model='gemini-2.0-flash-exp',
            contents=[
                prompt,
                Part.from_bytes(data=file_bytes, mime_type=mime_type)
            ]
        )
        extracted_text = response.text
        print(f"[DEBUG] Gemini response: {extracted_text[:200]}...")

        # Parse the JSON response
        if "```json" in extracted_text:
            json_str = extracted_text.split("```json")[1].split("```")[0].strip()
        elif "```" in extracted_text:
            json_str = extracted_text.split("```")[1].split("```")[0].strip()
        else:
            json_str = extracted_text.strip()

        extracted_data = json.loads(json_str)
        print(f"[DEBUG] Extracted data: {extracted_data}")

    except Exception as e:
        print(f"[ERROR] Extraction failed: {e}")
        import traceback
        traceback.print_exc()
        return {
            "error": f"Extraction failed: {str(e)}",
            "updated_schema": user_schema
        }

    # Update the user schema with extracted data IN PLACE
    _update_schema_from_extraction(user_schema, extracted_data, doc_type)

    # Identify missing required fields (excluding needs dict)
    missing_fields = _identify_missing_fields(user_schema)

    return {
        "updated_schema": user_schema,  # Return the reference (now modified)
        "extracted_data": extracted_data,
        "missing_fields": missing_fields,
        "is_complete": len(missing_fields) == 0,
        "success": True
    }


def _update_schema_from_extraction(schema: Dict, extracted_data: Dict, doc_type: str) -> None:
    """
    Update the user schema with extracted data IN PLACE

    Args:
        schema: The user schema to update (modified in place)
        extracted_data: Data extracted from document
        doc_type: Type of document processed

    Returns:
        None (modifies schema in place)
    """

    # Update trip fields
    if "tripType" in extracted_data:
        schema["tripType"] = extracted_data["tripType"]
    if "departureDate" in extracted_data:
        schema["departureDate"] = extracted_data["departureDate"]
    if "returnDate" in extracted_data:
        # Note: schema has departureDate but no returnDate field in template
        # Store it anyway for quote API
        schema["returnDate"] = extracted_data["returnDate"]
    if "departureCountry" in extracted_data:
        schema["departureCountry"] = extracted_data["departureCountry"]
    if "arrivalCountry" in extracted_data:
        schema["arrivalCountry"] = extracted_data["arrivalCountry"]
    if "adultsCount" in extracted_data:
        schema["adultsCount"] = extracted_data["adultsCount"]
    if "childrenCount" in extracted_data:
        schema["childrenCount"] = extracted_data["childrenCount"]

    # Update insured person (first in list) - typically from passport
    if doc_type in ["passport", "auto"]:
        if not schema["insureds"]:
            schema["insureds"] = [{}]

        insured = schema["insureds"][0]

        if "title" in extracted_data:
            insured["title"] = extracted_data["title"]
        if "firstName" in extracted_data:
            insured["firstName"] = extracted_data["firstName"]
        if "lastName" in extracted_data:
            insured["lastName"] = extracted_data["lastName"]
        if "nationality" in extracted_data:
            insured["nationality"] = extracted_data["nationality"]
        if "dateOfBirth" in extracted_data:
            insured["dateOfBirth"] = extracted_data["dateOfBirth"]
        if "passport" in extracted_data:
            insured["passport"] = extracted_data["passport"]
        if "email" in extracted_data:
            insured["email"] = extracted_data["email"]
        if "phoneNumber" in extracted_data:
            insured["phoneNumber"] = extracted_data["phoneNumber"]
        if "phoneType" in extracted_data:
            insured["phoneType"] = extracted_data["phoneType"]

        # Default id and relationship if not set
        if not insured.get("id"):
            insured["id"] = "1"
        if not insured.get("relationship"):
            insured["relationship"] = "main"

        schema["insureds"][0] = insured

        # Also fill mainContact with same info (typically same person)
        if "title" in extracted_data:
            schema["mainContact"]["title"] = extracted_data["title"]
        if "firstName" in extracted_data:
            schema["mainContact"]["firstName"] = extracted_data["firstName"]
        if "lastName" in extracted_data:
            schema["mainContact"]["lastName"] = extracted_data["lastName"]
        if "nationality" in extracted_data:
            schema["mainContact"]["nationality"] = extracted_data["nationality"]
        if "dateOfBirth" in extracted_data:
            schema["mainContact"]["dateOfBirth"] = extracted_data["dateOfBirth"]
        if "passport" in extracted_data:
            schema["mainContact"]["passport"] = extracted_data["passport"]
        if "email" in extracted_data:
            schema["mainContact"]["email"] = extracted_data["email"]
        if "phoneNumber" in extracted_data:
            schema["mainContact"]["phoneNumber"] = extracted_data["phoneNumber"]
        if "phoneType" in extracted_data:
            schema["mainContact"]["phoneType"] = extracted_data["phoneType"]
        if not schema["mainContact"].get("id"):
            schema["mainContact"]["id"] = "1"

    # Update contact info from itinerary
    if doc_type == "itinerary":
        if "email" in extracted_data:
            if schema["insureds"]:
                schema["insureds"][0]["email"] = extracted_data["email"]
            schema["mainContact"]["email"] = extracted_data["email"]
        if "phoneNumber" in extracted_data:
            if schema["insureds"]:
                schema["insureds"][0]["phoneNumber"] = extracted_data["phoneNumber"]
            schema["mainContact"]["phoneNumber"] = extracted_data["phoneNumber"]
            # Default to mobile
            if schema["insureds"]:
                schema["insureds"][0]["phoneType"] = "mobile"
            schema["mainContact"]["phoneType"] = "mobile"


def _identify_missing_fields(schema: Dict) -> List[str]:
    """
    Identify which required fields are still missing in the schema
    Focus ONLY on document magic agent's responsibility (NOT needs dict)

    Args:
        schema: The user schema to check

    Returns:
        List of missing field names with human-readable descriptions
    """
    missing = []

    # Required trip fields
    if not schema.get("tripType"):
        missing.append("Trip Type (ST for single trip or AN for annual)")
    if not schema.get("departureDate"):
        missing.append("Departure Date")
    if not schema.get("returnDate"):
        missing.append("Return Date")
    if not schema.get("departureCountry"):
        missing.append("Departure Country")
    if not schema.get("arrivalCountry"):
        missing.append("Arrival/Destination Country")
    if not schema.get("adultsCount") or schema.get("adultsCount") == 0:
        missing.append("Number of Adults")
    if schema.get("childrenCount") is None:
        missing.append("Number of Children (can be 0)")

    # Check if we have at least one insured person
    if not schema.get("insureds") or not schema["insureds"]:
        missing.append("At least one insured person")
    else:
        insured = schema["insureds"][0]
        if not insured.get("id"):
            missing.append("Insured Person ID")
        if not insured.get("title"):
            missing.append("Insured Title (Mr/Ms/Mrs)")
        if not insured.get("firstName"):
            missing.append("Insured First Name")
        if not insured.get("lastName"):
            missing.append("Insured Last Name")
        if not insured.get("nationality"):
            missing.append("Insured Nationality")
        if not insured.get("dateOfBirth"):
            missing.append("Insured Date of Birth")
        if not insured.get("passport"):
            missing.append("Insured Passport Number")
        if not insured.get("email"):
            missing.append("Insured Email")
        if not insured.get("phoneNumber"):
            missing.append("Insured Phone Number")
        if not insured.get("phoneType"):
            missing.append("Insured Phone Type (mobile/home)")
        if not insured.get("relationship"):
            missing.append("Insured Relationship (main/spouse/child/parent)")

    # Check main contact fields
    contact = schema.get("mainContact", {})
    if not contact.get("id"):
        missing.append("Main Contact ID")
    if not contact.get("title"):
        missing.append("Main Contact Title")
    if not contact.get("firstName"):
        missing.append("Main Contact First Name")
    if not contact.get("lastName"):
        missing.append("Main Contact Last Name")
    if not contact.get("nationality"):
        missing.append("Main Contact Nationality")
    if not contact.get("dateOfBirth"):
        missing.append("Main Contact Date of Birth")
    if not contact.get("passport"):
        missing.append("Main Contact Passport")
    if not contact.get("email"):
        missing.append("Main Contact Email")
    if not contact.get("phoneNumber"):
        missing.append("Main Contact Phone Number")
    if not contact.get("phoneType"):
        missing.append("Main Contact Phone Type")
    if not contact.get("address"):
        missing.append("Main Contact Address")
    if not contact.get("city"):
        missing.append("Main Contact City")
    if not contact.get("zipCode"):
        missing.append("Main Contact Zip/Postal Code")
    if not contact.get("countryCode"):
        missing.append("Main Contact Country Code")

    return missing


def get_quote(user_id: str) -> Dict:
    """
    Get insurance quote for user from Ancileo pricing API

    This is the main tool for the conversation agent to call.
    It loads the user's profile, gets a quote, and saves the quote to profile.

    Args:
        user_id: User ID to get quote for

    Returns:
        Dictionary with quote details including quoteId, offerId, pricing info
    """
    # Load profile from disk
    schema = load_profile(user_id)

    # Get quote
    result = get_insurance_quote(schema)

    # Store quote in user profile for later purchase
    if result.get("success"):
        schema["last_quote"] = result
        save_profile(user_id, schema)

    return result


def get_insurance_quote(schema: Dict) -> Dict:
    """
    Get insurance quote from Ancileo pricing API using data from schema

    Args:
        schema: The user schema with trip information

    Returns:
        Dictionary with quote details including quoteId, offerId, pricing info
    """

    api_url = "https://dev.api.ancileo.com/v1/travel/front/pricing"
    api_key = os.getenv("ANCILEO_API_KEY")

    if not api_key:
        return {
            "error": "ANCILEO_API_KEY not found in environment variables",
            "success": False
        }

    # Extract required fields from schema
    trip_type = schema.get("tripType")
    departure_date = schema.get("departureDate")
    return_date = schema.get("returnDate")
    departure_country = schema.get("departureCountry")
    arrival_country = schema.get("arrivalCountry")
    adults_count = schema.get("adultsCount", 0)
    children_count = schema.get("childrenCount", 0)

    # Validate required fields
    if not all([trip_type, departure_date, return_date, departure_country, arrival_country]):
        return {
            "error": "Missing required trip information. Need: tripType, departureDate, returnDate, departureCountry, arrivalCountry",
            "success": False
        }

    # Hardcoded fields as per requirements
    payload = {
        "market": "SG",
        "languageCode": "en",
        "channel": "white-label",
        "deviceType": "DESKTOP",
        "context": {
            "tripType": trip_type,
            "departureDate": departure_date,
            "returnDate": return_date,
            "departureCountry": departure_country,
            "arrivalCountry": arrival_country,
            "adultsCount": adults_count,
            "childrenCount": children_count
        }
    }

    headers = {
        "Content-Type": "application/json",
        "x-api-key": api_key
    }

    try:
        response = requests.post(api_url, json=payload, headers=headers)
        response.raise_for_status()

        quote_data = response.json()

        # Extract key information from the response
        quote_id = quote_data.get('id')
        offers = []

        if 'offerCategories' in quote_data:
            for category in quote_data['offerCategories']:
                if 'offers' in category:
                    for offer in category['offers']:
                        offers.append({
                            'offerId': offer.get('id'),
                            'productCode': offer.get('productCode'),
                            'productType': category.get('productType', 'travel-insurance'),
                            'unitPrice': offer.get('unitPrice'),
                            'currency': offer.get('currency'),
                            'productName': offer.get('productInformation', {}).get('title', ''),
                            'coverDates': offer.get('coverDates', {}),
                        })

        return {
            "success": True,
            "quoteId": quote_id,
            "offers": offers,
            "full_response": quote_data
        }

    except requests.exceptions.RequestException as e:
        return {
            "error": f"API request failed: {str(e)}",
            "success": False
        }
    except Exception as e:
        return {
            "error": f"Unexpected error: {str(e)}",
            "success": False
        }


def purchase_insurance(
    schema: Dict,
    quote_id: str,
    offer_id: str,
    product_code: str,
    unit_price: float,
    currency: str,
    quantity: int = 1,
    is_send_email: bool = True
) -> Dict:
    """
    Purchase insurance using Ancileo purchase API

    IMPORTANT: This should only be called AFTER payment has been successfully processed

    Args:
        schema: The user schema with insureds and mainContact information
        quote_id: Quote ID from pricing API
        offer_id: Offer ID from pricing API
        product_code: Product code from pricing API
        unit_price: Unit price from pricing API
        currency: Currency code (e.g., "SGD")
        quantity: Quantity (default: 1)
        is_send_email: Whether to send confirmation email (default: True)

    Returns:
        Dictionary with purchase confirmation details
    """

    api_url = "https://dev.api.ancileo.com/v1/travel/front/purchase"
    api_key = os.getenv("ANCILEO_API_KEY")

    if not api_key:
        return {
            "error": "ANCILEO_API_KEY not found in environment variables",
            "success": False
        }

    # Calculate total price
    total_price = unit_price * quantity

    # Hardcoded fields as per requirements
    payload = {
        "market": "SG",
        "languageCode": "en",
        "channel": "white-label",
        "quoteId": quote_id,
        "purchaseOffers": [
            {
                "productType": "travel-insurance",
                "offerId": offer_id,
                "productCode": product_code,
                "unitPrice": unit_price,
                "currency": currency,
                "quantity": quantity,
                "totalPrice": total_price,
                "isSendEmail": is_send_email
            }
        ],
        "insureds": schema.get("insureds", []),
        "mainContact": schema.get("mainContact", {})
    }

    headers = {
        "Content-Type": "application/json",
        "X-API-Key": api_key
    }

    try:
        response = requests.post(api_url, json=payload, headers=headers)
        response.raise_for_status()

        purchase_data = response.json()

        return {
            "success": True,
            "purchase_data": purchase_data
        }

    except requests.exceptions.RequestException as e:
        return {
            "error": f"API request failed: {str(e)}",
            "success": False
        }
    except Exception as e:
        return {
            "error": f"Unexpected error: {str(e)}",
            "success": False
        }
