"""
Tools for the Conversation Agent
These functions provide the core functionality for the insurance assistant
"""

import json
import requests
import os
import sys
import asyncio
from datetime import datetime
from typing import Dict, Optional, List

# Import the schema template
sys.path.append('/Users/ray/Desktop/hackdeez/backend/ai_backend')
from schema_template import taxonomy_dict

# Import profile manager for file-based storage
sys.path.append('/Users/ray/Desktop/hackdeez/backend/ai_backend')
from profile_manager import load_profile, save_profile, delete_profile

def check_pipeline_status(user_id: str) -> Dict:
    """
    Check if user profile is ready for next pipeline step (policy recommendations)

    CRITICAL: Call this IMMEDIATELY after document_magic_agent completes extraction
    This tells you whether to automatically trigger policy_recommendation_agent

    Args:
        user_id: The unique identifier for the user

    Returns:
        Dictionary with:
        - ready_for_policy_recs: bool - whether to trigger policy_recommendation_agent NOW
        - destination: str - arrival country code
        - departure_date: str - departure date
        - action: str - explicit instruction on what to do next
    """
    print(f"[DEBUG] check_pipeline_status called for user: {user_id}")

    profile = load_profile(user_id)

    # Check minimum requirements for policy recommendations
    has_destination = bool(profile.get('arrivalCountry'))
    has_date = bool(profile.get('departureDate') or profile.get('returnDate'))
    ready = has_destination and has_date

    destination = profile.get('arrivalCountry', '')
    departure_date = profile.get('departureDate', profile.get('returnDate', ''))

    print(f"[DEBUG] Pipeline status: ready={ready}, destination={destination}, date={departure_date}")

    if ready:
        action = f"TRIGGER POLICY RECOMMENDATIONS NOW! Immediately delegate to policy_recommendation_agent. Destination: {destination}, Date: {departure_date}"
    else:
        missing = []
        if not has_destination:
            missing.append("destination (arrivalCountry)")
        if not has_date:
            missing.append("travel dates (departureDate/returnDate)")
        action = f"Not ready yet. Still need: {', '.join(missing)}"

    return {
        "ready_for_policy_recs": ready,
        "destination": destination,
        "departure_date": departure_date,
        "action": action
    }

def get_user_data(user_id: str) -> Dict:
    """
    Retrieve user profile data from file-based storage

    Args:
        user_id: The unique identifier for the user

    Returns:
        Dictionary containing the user's profile data based on schema_template
    """
    # Load profile from file (creates new from template if doesn't exist)
    return load_profile(user_id)

def setup_insureds_from_counts(user_id: str) -> Dict:
    """
    Dynamically create insureds entries based on adultsCount and childrenCount.

    This should be called AFTER document extraction or trip info collection when
    we know how many travelers there are. It will:
    1. Port mainContact → insureds[0] (the account holder is always first insured)
    2. Create empty entries for additional travelers (adultsCount + childrenCount - 1)

    Args:
        user_id: The unique identifier for the user

    Returns:
        Dict with success status, counts, and updated profile
    """
    profile = get_user_data(user_id)
    main_contact = profile.get('mainContact', {})

    adults_count = profile.get('adultsCount', 0)
    children_count = profile.get('childrenCount', 0)
    total_travelers = adults_count + children_count

    if total_travelers == 0:
        return {
            'success': False,
            'error': 'No traveler count found in profile',
            'message': 'Please provide trip details first (how many travelers?)'
        }

    # Initialize insureds array
    profile['insureds'] = []

    # First insured is always the mainContact (account holder)
    first_insured = {}
    fields_to_port = [
        'id', 'title', 'firstName', 'lastName', 'nationality',
        'dateOfBirth', 'passport', 'email', 'phoneType', 'phoneNumber'
    ]

    ported_fields = []
    for field in fields_to_port:
        if main_contact.get(field):
            first_insured[field] = main_contact[field]
            ported_fields.append(field)

    first_insured['relationship'] = 'main'
    profile['insureds'].append(first_insured)

    # Create empty entries for additional travelers
    for i in range(1, total_travelers):
        empty_insured = {
            "id": "",
            "title": "",
            "firstName": "",
            "lastName": "",
            "nationality": "",
            "dateOfBirth": "",
            "passport": "",
            "email": "",
            "phoneType": "",
            "phoneNumber": "",
            "relationship": ""
        }
        profile['insureds'].append(empty_insured)

    # Save profile to file
    save_profile(user_id, profile)

    return {
        'success': True,
        'total_travelers': total_travelers,
        'adults_count': adults_count,
        'children_count': children_count,
        'insureds_count': len(profile['insureds']),
        'ported_fields': ported_fields,
        'updated_profile': profile,
        'message': f"Created {len(profile['insureds'])} traveler entries. Main traveler info populated. {len(profile['insureds']) - 1} additional travelers need details."
    }

def fill_information(user_id: str, user_message: str) -> Dict:
    """
    Intelligently extract ALL possible information from user's message and update profile.
    Uses LLM to parse natural language and map to profile fields.

    Args:
        user_id: The unique identifier for the user
        user_message: The user's natural language message

    Returns:
        Dict with extracted_fields, updated_profile, and missing_fields
    """
    from google import genai

    profile = get_user_data(user_id)

    # Use Gemini to extract structured information from natural language
    client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

    extraction_prompt = f"""You are an information extraction assistant. Extract ALL travel and personal information from the user's message and map it to the profile fields.

User message: "{user_message}"

Current profile state (only update fields that are mentioned or implied):
- Trip fields (top-level): departureDate, returnDate, departureCountry, arrivalCountry, tripType (ST=single, AN=annual), adultsCount, childrenCount
- Insured person fields (use "insureds.0." prefix): nationality, dateOfBirth, passport, email, phoneNumber, phoneType, title (Mr/Mrs/Ms)
- Main contact fields (use "mainContact." prefix): email, phoneNumber, phoneType, address, city, zipCode, countryCode

IMPORTANT:
- Do NOT extract firstName or lastName - already in the system
- Contact info (email, phone, address) should use "mainContact." prefix
- Personal info for the traveler should use "insureds.0." prefix

Extract information and return ONLY valid JSON (no markdown, no explanation) in this exact format:
{{
  "extracted_fields": {{
    "field_name": "value",
    ...
  }},
  "confidence": "high/medium/low"
}}

Rules:
- Dates must be YYYY-MM-DD format
- Country names → 2-letter codes (Japan→JP, Singapore→SG, USA→US, etc.)
- Only include fields you found in the message
- If user says "next week" or relative dates, calculate the actual date
- Extract implicit information (e.g., "flying to Tokyo" → arrivalCountry: "JP")
- If adultsCount not mentioned but user says "I" → adultsCount: 1
- Contact info goes in mainContact: "mainContact.email", "mainContact.phoneNumber", "mainContact.address", "mainContact.city", "mainContact.zipCode", "mainContact.countryCode"
- Traveler personal info goes in insureds: "insureds.0.email", "insureds.0.dateOfBirth", "insureds.0.passport", "insureds.0.nationality"

Examples:
"I'm going to Japan next month for 2 weeks" → {{"departureDate": "2025-12-01", "returnDate": "2025-12-15", "arrivalCountry": "JP", "tripType": "ST", "adultsCount": 1}}
"My wife and I are traveling to Paris" → {{"arrivalCountry": "FR", "adultsCount": 2}}
"My email is john@email.com and phone is +65 91234567" → {{"mainContact.email": "john@email.com", "mainContact.phoneNumber": "+65 91234567", "insureds.0.email": "john@email.com", "insureds.0.phoneNumber": "+65 91234567"}}
"I live at 123 Main St, Singapore 238858" → {{"mainContact.address": "123 Main St", "mainContact.city": "Singapore", "mainContact.zipCode": "238858", "mainContact.countryCode": "SG"}}
"I was born Jan 5 1990, passport A1234567" → {{"insureds.0.dateOfBirth": "1990-01-05", "insureds.0.passport": "A1234567"}}
"""

    try:
        response = client.models.generate_content(
            model='gemini-2.0-flash-exp',
            contents=extraction_prompt
        )

        extracted_text = response.text.strip()

        # Clean up markdown code blocks if present
        if "```json" in extracted_text:
            extracted_text = extracted_text.split("```json")[1].split("```")[0].strip()
        elif "```" in extracted_text:
            extracted_text = extracted_text.split("```")[1].split("```")[0].strip()

        extraction_result = json.loads(extracted_text)
        extracted_fields = extraction_result.get("extracted_fields", {})

        # Update profile with extracted fields
        updates_made = []
        for field_name, field_value in extracted_fields.items():
            # Handle nested fields (e.g., "insureds.0.firstName")
            if '.' in field_name:
                parts = field_name.split('.')
                current = profile
                for part in parts[:-1]:
                    if part.isdigit():  # Array index
                        idx = int(part)
                        if idx >= len(current):
                            current.append({})
                        current = current[idx]
                    else:
                        if part not in current:
                            current[part] = {}
                        current = current[part]
                current[parts[-1]] = field_value
            else:
                profile[field_name] = field_value

            updates_made.append(f"{field_name}={field_value}")

        # Save profile to file
        save_profile(user_id, profile)

        # Identify missing critical fields
        missing = _identify_missing_fields(profile)

        return {
            "success": True,
            "extracted_fields": extracted_fields,
            "updates_made": updates_made,
            "updated_profile": profile,
            "missing_fields": missing,
            "confidence": extraction_result.get("confidence", "medium")
        }

    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "extracted_fields": {},
            "updated_profile": profile,
            "missing_fields": _identify_missing_fields(profile)
        }


def _identify_missing_fields(profile: Dict) -> List[str]:
    """Helper to identify which critical fields are still missing"""
    missing = []

    # Critical trip fields
    if not profile.get("departureDate"):
        missing.append("departure date")
    if not profile.get("arrivalCountry"):
        missing.append("destination country")
    if not profile.get("adultsCount") or profile.get("adultsCount") == 0:
        missing.append("number of travelers")

    # Check if we have at least basic personal info
    insureds = profile.get("insureds", [])
    if not insureds or not insureds[0].get("firstName"):
        missing.append("traveler name")
    if not insureds or not insureds[0].get("email"):
        missing.append("email address")

    # Contact details for purchase
    main_contact = profile.get("mainContact", {})
    if not main_contact.get("address"):
        missing.append("contact address")

    return missing

def call_pricing_api(user_id: str) -> Dict:
    """
    Call the Ancileo pricing API to get insurance quotes

    Args:
        user_id: The user ID to get pricing for

    Returns:
        API response containing quoteId, offerId, and pricing information
    """


    # Get user profile
    user_profile = get_user_data(user_id)

    # Extract required fields from profile
    trip_data = {
        "market": "SG",  # Hardcoded as specified
        "languageCode": "en",  # Hardcoded
        "channel": "white-label",  # Hardcoded
        "deviceType": "DESKTOP",  # Hardcoded
        "context": {
            "tripType": user_profile.get("tripType", "ST"),
            "departureDate": user_profile.get("departureDate", ""),
            "returnDate": user_profile.get("returnDate", user_profile.get("departureDate", "")),  # Use departure if no return
            "departureCountry": user_profile.get("departureCountry", "SG"),
            "arrivalCountry": user_profile.get("arrivalCountry", ""),
            "adultsCount": user_profile.get("adultsCount", 1),
            "childrenCount": user_profile.get("childrenCount", 0)
        }
    }

    # Validate required fields
    if not trip_data["context"]["departureDate"] or not trip_data["context"]["arrivalCountry"]:
        missing = [f for f in ["departureDate", "arrivalCountry"] if not trip_data["context"].get(f)]
        return {
            "error": "Missing required trip information",
            "missing_fields": missing
        }


    # Call the REAL Ancileo pricing API
    api_key = os.getenv("ANCILIEO_API_KEY")  # Note: typo in env var name
    if not api_key:
        return {
            "error": "API key not configured",
            "message": "ANCILIEO_API_KEY not found in environment"
        }

    headers = {
        "Content-Type": "application/json",
        "x-api-key": api_key
    }

    try:
        response = requests.post(
            "https://dev.api.ancileo.com/v1/travel/front/pricing",
            json=trip_data,
            headers=headers,
            timeout=30
        )

        if response.status_code != 200:
            return {
                "error": f"Pricing API error: {response.status_code}",
                "message": response.text
            }

        pricing_data = response.json()

        # Extract and restructure for easier use in purchase
        quote_id = pricing_data.get('id')
        offers = pricing_data.get('offerCategories', [{}])[0].get('offers', [])

        if not offers:
            return {
                "error": "No insurance offers available",
                "message": "No offers returned from pricing API"
            }

        # Store the complete pricing response for purchase API
        user_profile["last_quote"] = {
            "quoteId": quote_id,
            "pricing_response": pricing_data,
            "offers": offers,
            "selected_offer": offers[0]  # Default to first offer
        }

        # Save profile to file
        save_profile(user_id, user_profile)

        return {
            "success": True,
            "quoteId": quote_id,
            "offers": offers,
            "message": f"Retrieved {len(offers)} insurance quote(s)"
        }

    except requests.exceptions.Timeout:
        return {
            "error": "Request timeout",
            "message": "Pricing API request timed out after 30 seconds"
        }
    except Exception as e:
        return {
            "error": "API call failed",
            "message": str(e)
        }

def call_purchase_api(user_id: str, payment_confirmed: bool = False) -> Dict:
    """
    Call the Ancileo purchase API to complete insurance purchase

    IMPORTANT: Only call this after make_payment returns success=True

    Args:
        user_id: The user ID to purchase for
        payment_confirmed: Whether payment has been processed (must be True)

    Returns:
        Purchase confirmation or error
    """


    # Get user profile
    user_profile = get_user_data(user_id)

    # Check if payment was actually completed
    payment_status = user_profile.get("payment_status")
    if payment_status != "completed":
        return {
            "error": "Payment not completed",
            "message": "Please complete payment using make_payment tool first before purchasing"
        }

    if not payment_confirmed:
        return {
            "error": "Payment not confirmed",
            "message": "Please set payment_confirmed=True after successful payment"
        }

    # Check if we have quote data stored in the profile
    quote_data = user_profile.get("last_quote", {})
    if not quote_data:
        return {
            "error": "No quote found",
            "message": "Please get a pricing quote first before purchasing"
        }

    # Extract insureds and mainContact from profile
    insureds = user_profile.get("insureds", [])
    main_contact = user_profile.get("mainContact", {})

    # Validate required fields
    if not insureds or not all([main_contact.get(f) for f in ["firstName", "lastName", "email"]]):
        return {
            "error": "Missing required personal information",
            "message": "Please provide complete insured and contact details"
        }

    # Get the selected offer from the stored quote
    selected_offer = quote_data.get("selected_offer", {})
    if not selected_offer:
        offers = quote_data.get("offers", [])
        selected_offer = offers[0] if offers else {}

    if not selected_offer:
        return {
            "error": "No offer selected",
            "message": "Quote data does not contain a valid offer"
        }

    purchase_data = {
        "market": "SG",
        "languageCode": "en",
        "channel": "white-label",
        "quoteId": quote_data.get("quoteId"),
        "purchaseOffers": [{
            "productType": "travel-insurance",
            "offerId": selected_offer.get("id"),  # Use 'id' from offer, not 'offerId'
            "productCode": selected_offer.get("productCode"),
            "unitPrice": selected_offer.get("unitPrice"),
            "currency": selected_offer.get("currency", "SGD"),
            "quantity": 1,
            "totalPrice": selected_offer.get("unitPrice"),
            "isSendEmail": True
        }],
        "insureds": insureds,
        "mainContact": main_contact
    }

    # Call the REAL Ancileo purchase API
    api_key = os.getenv("ANCILIEO_API_KEY")  # Note: typo in env var name
    if not api_key:
        return {
            "error": "API key not configured",
            "message": "ANCILIEO_API_KEY not found in environment"
        }

    headers = {
        "Content-Type": "application/json",
        "X-API-Key": api_key
    }

    try:
        response = requests.post(
            "https://dev.api.ancileo.com/v1/travel/front/purchase",
            json=purchase_data,
            headers=headers,
            timeout=30
        )

        if response.status_code != 200:
            return {
                "error": f"Purchase API error: {response.status_code}",
                "message": response.text,
                "request_payload": purchase_data  # Include for debugging
            }

        purchase_result = response.json()

        # Extract purchased offer details
        purchased_offers = purchase_result.get("purchasedOffers", [])
        if purchased_offers:
            purchased_offer = purchased_offers[0]
            policy_id = purchased_offer.get("purchasedOfferId")

            return {
                "success": True,
                "policyId": policy_id,
                "quoteId": purchase_result.get("quoteId"),
                "purchasedOffers": purchased_offers,
                "confirmationEmail": main_contact.get("email"),
                "message": f"Insurance purchased successfully! Policy ID: {policy_id}. Confirmation sent to {main_contact.get('email')}"
            }
        else:
            return {
                "success": True,
                "response": purchase_result,
                "message": "Purchase completed"
            }

    except requests.exceptions.Timeout:
        return {
            "error": "Request timeout",
            "message": "Purchase API request timed out after 30 seconds"
        }
    except Exception as e:
        return {
            "error": "API call failed",
            "message": str(e),
            "request_payload": purchase_data  # Include for debugging
        }


def make_payment(user_id: str, amount_cents: int, description: str = "Travel Insurance") -> Dict:
    """
    Process payment through Stripe MCP endpoint

    This tool calls the payment gateway to process the insurance payment.
    The agent should call this BEFORE calling call_purchase_api.

    Args:
        user_id: The user ID to process payment for
        amount_cents: Payment amount in cents (e.g., 5000 = $50.00)
        description: Description of the payment (optional)

    Returns:
        Payment result with success status
    """


    # Get user profile for email
    user_profile = get_user_data(user_id)
    main_contact = user_profile.get("mainContact", {})
    customer_email = main_contact.get("email")

    if not customer_email:
        return {
            "success": False,
            "error": "Missing customer email",
            "message": "Please provide your email address first"
        }

    # Get quote data for payment reference
    quote_data = user_profile.get("last_quote", {})
    if not quote_data:
        return {
            "success": False,
            "error": "No quote found",
            "message": "Please get a pricing quote first"
        }

    # Generate payment ID based on quote
    payment_id = f"payment_{user_id}_{quote_data.get('quoteId', 'unknown')[:8]}"

    # Prepare payment request
    payment_data = {
        "paymentId": payment_id,
        "amountCents": amount_cents,
        "currency": "sgd",
        "customerEmail": customer_email,
        "description": description
    }


    try:
        # Call payment service endpoint
        response = requests.post(
            "http://localhost:8080/paymentpage/payments",
            json=payment_data,
            headers={"Content-Type": "application/json"},
            timeout=30
        )

        if response.status_code == 200:
            payment_response = response.json()
            client_secret = payment_response.get("clientSecret")

            # TODO: In production, payment should only be marked "completed" after webhook confirmation
            # For now, we're mocking the payment as immediately completed for testing
            user_profile["payment_status"] = "completed"
            user_profile["payment_id"] = payment_id
            user_profile["payment_amount"] = amount_cents
            user_profile["payment_client_secret"] = client_secret

            # Save profile to file
            save_profile(user_id, user_profile)

            return {
                "success": True,
                "payment_id": payment_id,
                "client_secret": client_secret,
                "amount": amount_cents / 100,
                "currency": "SGD",
                "status": "completed",  # MOCKED: Should be "pending" until webhook confirms
                "message": f"Payment of ${amount_cents/100:.2f} SGD processed successfully! (Mock: Auto-completed for testing)"
            }
        else:
            return {
                "success": False,
                "error": f"Payment failed with status {response.status_code}",
                "message": "Payment processing failed. Please try again.",
                "details": response.text
            }

    except requests.exceptions.ConnectionError:
        return {
            "success": False,
            "error": "Payment gateway unavailable",
            "message": "Cannot connect to payment service. Please ensure the payment server is running on port 8080."
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "message": "An error occurred during payment processing."
        }


def check_payment_status(user_id: str) -> Dict:
    """
    Check the status of a payment via the payment service

    This function polls the payment service to check if a payment has been completed.
    Useful for webhook-free status checking.

    Args:
        user_id: The user ID to check payment status for

    Returns:
        Payment status information
    """
    user_profile = get_user_data(user_id)
    payment_id = user_profile.get("payment_id")

    if not payment_id:
        return {
            "success": False,
            "error": "No payment found",
            "message": "No payment has been initiated for this user"
        }

    try:
        # Call payment service status endpoint
        response = requests.get(
            f"http://localhost:8080/paymentpage/status/{payment_id}",
            timeout=10
        )

        if response.status_code == 200:
            status_data = response.json()
            payment_status = status_data.get("status")

            # Update profile with latest status
            user_profile["payment_status"] = payment_status
            save_profile(user_id, user_profile)

            return {
                "success": True,
                "payment_id": payment_id,
                "status": payment_status,
                "message": f"Payment status: {payment_status}"
            }
        else:
            return {
                "success": False,
                "error": f"Status check failed with code {response.status_code}",
                "message": "Could not check payment status"
            }

    except requests.exceptions.ConnectionError:
        return {
            "success": False,
            "error": "Payment service unavailable",
            "message": "Cannot connect to payment service on port 8080"
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "message": "Error checking payment status"
        }