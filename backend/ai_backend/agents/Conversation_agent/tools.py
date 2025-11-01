"""
Tools for the Conversation Agent
These functions provide the core functionality for the insurance assistant
"""

import json
import requests
import os
import sys
from datetime import datetime
from typing import Dict, Optional, List

# Import the schema template
sys.path.append('/Users/ray/Desktop/hackdeez/backend/ai_backend')
from schema_template import taxonomy_dict

# Simple in-memory storage for now (can be replaced with actual DB later)
user_profiles = {}

def get_user_data(user_id: str) -> Dict:
    """
    Retrieve user profile data from storage

    Args:
        user_id: The unique identifier for the user

    Returns:
        Dictionary containing the user's profile data based on schema_template
    """
    if user_id not in user_profiles:
        # Initialize new user with empty template
        user_profiles[user_id] = taxonomy_dict.copy()
        print(f"Created new profile for user {user_id}")

    return user_profiles[user_id]

def fill_information(user_id: str, field_updates: Dict) -> Dict:
    """
    Update user profile with new information

    Args:
        user_id: The unique identifier for the user
        field_updates: Dictionary of fields to update in the profile

    Returns:
        Updated user profile
    """
    profile = get_user_data(user_id)

    # Update the profile with new data
    for key, value in field_updates.items():
        if key in profile:
            if isinstance(profile[key], dict):
                # For nested dictionaries like 'needs' or 'mainContact'
                profile[key].update(value)
            else:
                profile[key] = value

    # Save back to storage
    user_profiles[user_id] = profile
    print(f"Updated profile for user {user_id}")

    return profile

def call_pricing_api(user_profile: Dict) -> Dict:
    """
    Call the Ancileo pricing API to get insurance quotes

    Args:
        user_profile: The user's complete profile with trip details

    Returns:
        API response containing quoteId, offerId, and pricing information
    """

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
        return {
            "error": "Missing required trip information",
            "missing_fields": [
                f for f in ["departureDate", "arrivalCountry"]
                if not trip_data["context"].get(f)
            ]
        }

    # Mock response for now (replace with actual API call)
    # In production, uncomment the following:
    # api_key = os.getenv("ANCILEO_API_KEY")
    # headers = {
    #     "Content-Type": "application/json",
    #     "x-api-key": api_key
    # }
    # response = requests.post(
    #     "https://dev.api.ancileo.com/v1/travel/front/pricing",
    #     json=trip_data,
    #     headers=headers
    # )
    # return response.json()

    # Mock successful response
    return {
        "id": "613d6afb-d34c-43aa-80fc-05eede925c61",
        "quoteId": "9473a27b-7c46-4870-9e33-aea613942d28",
        "offers": [{
            "id": "22539aa6-5abe-4bfb-9156-35d4e1a77cfd",
            "offerId": "f80dfc75-36e3-433a-b561-f182383cd342",
            "productCode": "SG_AXA_SCOOT_COMP",
            "unitPrice": 17.6,
            "currency": "SGD",
            "productName": "Scootsurance - Travel Insurance",
            "coverDates": {
                "from": trip_data["context"]["departureDate"],
                "to": trip_data["context"]["returnDate"]
            }
        }]
    }

def call_purchase_api(quote_data: Dict, user_profile: Dict, payment_confirmed: bool = False) -> Dict:
    """
    Call the Ancileo purchase API to complete insurance purchase

    Args:
        quote_data: Response from pricing API containing quoteId and offerId
        user_profile: Complete user profile with insureds and mainContact
        payment_confirmed: Whether payment has been processed

    Returns:
        Purchase confirmation or error
    """

    if not payment_confirmed:
        return {
            "error": "Payment not confirmed",
            "message": "Please complete payment before purchase"
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

    purchase_data = {
        "market": "SG",
        "languageCode": "en",
        "channel": "white-label",
        "quoteId": quote_data.get("quoteId"),
        "purchaseOffers": [{
            "productType": "travel-insurance",
            "offerId": quote_data.get("offers", [{}])[0].get("offerId"),
            "productCode": quote_data.get("offers", [{}])[0].get("productCode"),
            "unitPrice": quote_data.get("offers", [{}])[0].get("unitPrice"),
            "currency": quote_data.get("offers", [{}])[0].get("currency", "SGD"),
            "quantity": 1,
            "totalPrice": quote_data.get("offers", [{}])[0].get("unitPrice"),
            "isSendEmail": True
        }],
        "insureds": insureds,
        "mainContact": main_contact
    }

    # Mock response for now (replace with actual API call)
    # In production, uncomment:
    # api_key = os.getenv("ANCILEO_API_KEY")
    # headers = {
    #     "Content-Type": "application/json",
    #     "X-API-Key": api_key
    # }
    # response = requests.post(
    #     "https://dev.api.ancileo.com/v1/travel/front/purchase",
    #     json=purchase_data,
    #     headers=headers
    # )
    # return response.json()

    # Mock successful response
    return {
        "status": "success",
        "policyNumber": "POL-2025-001234",
        "confirmationEmail": main_contact.get("email"),
        "message": f"Insurance purchased successfully. Confirmation sent to {main_contact.get('email')}"
    }