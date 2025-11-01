"""
Test script for Document Magic Agent
Tests document extraction, quote retrieval, and purchase functionality
"""

import os
import sys
from typing import Dict
from dotenv import load_dotenv

# Load environment variables
env_path = os.path.join(os.path.dirname(__file__), '../../../../.env')
load_dotenv(env_path)

# Handle typo in .env file - ANCILIO vs ANCILEO
if os.getenv("ANCILIO_API_KEY") and not os.getenv("ANCILEO_API_KEY"):
    os.environ["ANCILEO_API_KEY"] = os.getenv("ANCILIO_API_KEY")

# Add parent directories to path to import the agent
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../../')))

from agents.Conversation_agent.helper_agents.document_magic_agent.tools import (
    process_document,
    get_quote,
    purchase_insurance,
    extract_and_fill_profile,
    _identify_missing_fields
)
from agents.Conversation_agent.helper_agents.document_magic_agent.artifact_manager import (
    load_user_artifact,
    save_user_artifact,
    get_artifact_path,
    delete_user_artifact
)
from schema_template import taxonomy_dict


def convert_file_to_base64(file_path: str) -> str:
    """Convert a file to base64 string"""
    import base64
    with open(file_path, 'rb') as f:
        return base64.b64encode(f.read()).decode('utf-8')


def test_extract_and_fill_profile():
    """Test document extraction with real sample documents using file-based artifact"""
    print("\n=== Testing process_document with File-Based Artifact ===")

    # Check if GEMINI_API_KEY is set
    if not os.getenv("GEMINI_API_KEY"):
        print("WARNING: GEMINI_API_KEY not set in environment")
        print("Skipping document extraction test.")
        return

    # Test user ID
    test_user_id = "test_user_1"

    # Clean up any existing test artifact
    delete_user_artifact(test_user_id)

    # Paths to sample files
    sample_passport = os.path.join(os.path.dirname(__file__), '../../../../sample_data/sample_passport/sample1.png')
    sample_itinerary = os.path.join(os.path.dirname(__file__), '../../../../sample_data/sample_itineraries/Bali_Adventure_Honeymoon.pdf')

    print(f"\n🆔 Test User: {test_user_id}")
    print(f"📁 Artifact will be saved to: {get_artifact_path(test_user_id)}")

    print("\nTest 1: Real Passport Extraction (sample1.png)")
    if os.path.exists(sample_passport):
        print(f"Loading passport from: {sample_passport}")
        passport_base64 = convert_file_to_base64(sample_passport)
        result = process_document(test_user_id, passport_base64, "passport")

        if 'error' in result:
            print(f"Error: {result.get('error')}")
        else:
            print(f"✓ Success: {result.get('success')}")
            print(f"\n✓ Updated Schema - insureds[0]:")
            insured = result['updated_schema']['insureds'][0]
            for key, value in insured.items():
                if value:  # Only show filled fields
                    print(f"  - {key}: {value}")

            print(f"\n✓ Updated Schema - mainContact (partial):")
            contact = result['updated_schema']['mainContact']
            for key in ['firstName', 'lastName', 'nationality', 'dateOfBirth', 'passport']:
                if contact.get(key):
                    print(f"  - {key}: {contact[key]}")

            print(f"\n✓ Missing Fields ({len(result.get('missing_fields', []))} fields):")
            for field in result.get('missing_fields', [])[:8]:  # Show first 8
                print(f"  - {field}")
            if len(result.get('missing_fields', [])) > 8:
                print(f"  ... and {len(result.get('missing_fields', [])) - 8} more")
            print(f"\n✓ Is Complete: {result.get('is_complete')}")
            print(f"\n💾 Artifact saved to: {result.get('artifact_path')}")
    else:
        print(f"⚠️  Sample passport not found at: {sample_passport}")
        return

    print("\n" + "="*60)
    print("\nTest 2: Real Itinerary Extraction (Bali_Adventure_Honeymoon.pdf)")
    print("Loading artifact from disk (should have passport data)...")
    if os.path.exists(sample_itinerary):
        print(f"Loading itinerary from: {sample_itinerary}")

        itinerary_base64 = convert_file_to_base64(sample_itinerary)
        result = process_document(test_user_id, itinerary_base64, "itinerary")

        if 'error' in result:
            print(f"Error: {result.get('error')}")
        else:
            print(f"✓ Success: {result.get('success')}")
            print(f"\n✓ Updated Schema - Trip Info:")
            schema = result['updated_schema']
            for key in ['tripType', 'departureDate', 'returnDate', 'departureCountry', 'arrivalCountry', 'adultsCount', 'childrenCount']:
                if schema.get(key):
                    print(f"  - {key}: {schema[key]}")

            print(f"\n✓ Missing Fields ({len(result.get('missing_fields', []))} fields):")
            for field in result.get('missing_fields', [])[:8]:
                print(f"  - {field}")
            if len(result.get('missing_fields', [])) > 8:
                print(f"  ... and {len(result.get('missing_fields', [])) - 8} more")
            print(f"\n✓ Is Complete: {result.get('is_complete')}")

            # Print the full artifact
            print("\n" + "="*60)
            print("FINAL USER SCHEMA ARTIFACT (after passport + itinerary)")
            print("="*60)
            final_schema = result['updated_schema']

            print("\n📋 TRIP INFO:")
            print(f"  tripType: {final_schema.get('tripType', 'NOT SET')}")
            print(f"  departureDate: {final_schema.get('departureDate', 'NOT SET')}")
            print(f"  returnDate: {final_schema.get('returnDate', 'NOT SET')}")
            print(f"  departureCountry: {final_schema.get('departureCountry', 'NOT SET')}")
            print(f"  arrivalCountry: {final_schema.get('arrivalCountry', 'NOT SET')}")
            print(f"  adultsCount: {final_schema.get('adultsCount', 'NOT SET')}")
            print(f"  childrenCount: {final_schema.get('childrenCount', 'NOT SET')}")

            print("\n👤 INSURED PERSON [0]:")
            if final_schema.get('insureds'):
                insured = final_schema['insureds'][0]
                for key, value in insured.items():
                    status = value if value else "NOT SET"
                    print(f"  {key}: {status}")
            else:
                print("  NOT SET")

            print("\n📞 MAIN CONTACT:")
            contact = final_schema.get('mainContact', {})
            for key, value in contact.items():
                status = value if value else "NOT SET"
                print(f"  {key}: {status}")

            print("\n🔍 NEEDS DICT (should be untouched by document magic agent):")
            needs = final_schema.get('needs', {})
            true_count = sum(1 for v in needs.values() if v)
            false_count = sum(1 for v in needs.values() if not v)
            print(f"  Total needs: {len(needs)}")
            print(f"  Set to True: {true_count}")
            print(f"  Set to False: {false_count}")
            print(f"  ✓ Correctly untouched: {true_count == 0}")

            print(f"\n💾 Final artifact saved to: {result.get('artifact_path')}")
            print(f"\n✨ You can inspect the artifact at:")
            print(f"   cat {result.get('artifact_path')}")

    else:
        print(f"⚠️  Sample itinerary not found at: {sample_itinerary}")


def test_missing_fields_identification():
    """Test the missing fields identification logic"""
    print("\n=== Testing _identify_missing_fields ===")

    import copy

    # Test with partial schema
    partial_schema = copy.deepcopy(taxonomy_dict)
    partial_schema["insureds"] = [{
        "firstName": "John",
        "lastName": "Doe",
        "nationality": "SG",
        "id": "",
        "title": "",
        "dateOfBirth": "",
        "passport": "",
        "email": "",
        "phoneType": "",
        "phoneNumber": "",
        "relationship": ""
    }]

    missing = _identify_missing_fields(partial_schema)
    print(f"\nPartial schema test - Missing fields count: {len(missing)}")
    print("First 5 missing fields:")
    for field in missing[:5]:
        print(f"  - {field}")

    # Test with complete schema
    complete_schema = copy.deepcopy(taxonomy_dict)
    complete_schema["tripType"] = "ST"
    complete_schema["departureDate"] = "2025-11-01"
    complete_schema["returnDate"] = "2025-11-15"
    complete_schema["departureCountry"] = "SG"
    complete_schema["arrivalCountry"] = "JP"
    complete_schema["adultsCount"] = 2
    complete_schema["childrenCount"] = 1
    complete_schema["insureds"] = [{
        "id": "1",
        "title": "Mr",
        "firstName": "John",
        "lastName": "Doe",
        "nationality": "SG",
        "dateOfBirth": "1990-01-01",
        "passport": "E1234567",
        "email": "john@example.com",
        "phoneNumber": "91234567",
        "phoneType": "mobile",
        "relationship": "main"
    }]
    complete_schema["mainContact"] = {
        "id": "1",
        "title": "Mr",
        "firstName": "John",
        "lastName": "Doe",
        "nationality": "SG",
        "dateOfBirth": "1990-01-01",
        "passport": "E1234567",
        "email": "john@example.com",
        "phoneNumber": "91234567",
        "phoneType": "mobile",
        "address": "123 Main St",
        "city": "Singapore",
        "zipCode": "123456",
        "countryCode": "SG"
    }

    missing = _identify_missing_fields(complete_schema)
    print(f"\nComplete schema test - Missing fields: {missing}")


def test_get_insurance_quote():
    """Test insurance quote API call with schema"""
    print("\n=== Testing get_insurance_quote with Schema ===")

    # Check if API key is set
    api_key = os.getenv("ANCILEO_API_KEY")
    if not api_key:
        print("WARNING: ANCILEO_API_KEY not set in environment")
        print("Skipping API test. Set the key to test the actual API call.")
        return

    import copy
    # Create a schema with trip info filled
    user_schema = copy.deepcopy(taxonomy_dict)
    user_schema["tripType"] = "ST"
    user_schema["departureDate"] = "2026-03-20"
    user_schema["returnDate"] = "2026-03-26"
    user_schema["departureCountry"] = "SG"
    user_schema["arrivalCountry"] = "ID"
    user_schema["adultsCount"] = 2
    user_schema["childrenCount"] = 0

    print("\nCalling pricing API with schema data...")
    print(f"Trip: {user_schema['departureCountry']} -> {user_schema['arrivalCountry']}")
    print(f"Dates: {user_schema['departureDate']} to {user_schema['returnDate']}")
    print(f"Passengers: {user_schema['adultsCount']} adults, {user_schema['childrenCount']} children")

    result = get_insurance_quote(user_schema)

    print(f"\nSuccess: {result.get('success')}")
    if result.get('success'):
        print(f"Quote ID: {result.get('quoteId')}")
        print(f"Number of offers: {len(result.get('offers', []))}")
        for i, offer in enumerate(result.get('offers', []), 1):
            print(f"\nOffer {i}:")
            print(f"  Product Name: {offer.get('productName')}")
            print(f"  Offer ID: {offer.get('offerId')}")
            print(f"  Product Code: {offer.get('productCode')}")
            print(f"  Price: {offer.get('currency')} {offer.get('unitPrice')}")
    else:
        print(f"Error: {result.get('error')}")


def test_purchase_insurance():
    """Test insurance purchase API call"""
    print("\n=== Testing purchase_insurance ===")

    # Check if API key is set
    api_key = os.getenv("ANCILEO_API_KEY")
    if not api_key:
        print("WARNING: ANCILEO_API_KEY not set in environment")
        print("Skipping API test. Set the key to test the actual API call.")
        return

    print("\n⚠️  NOTE: This is a mock test with dummy data.")
    print("To test for real, you need:")
    print("1. A valid quoteId from get_insurance_quote")
    print("2. A valid offerId from the quote response")
    print("3. Confirmed payment")

    # Mock data - this will likely fail without real quote ID
    mock_insureds = [
        {
            "id": "1",
            "title": "Mr",
            "firstName": "John",
            "lastName": "Doe",
            "nationality": "SG",
            "dateOfBirth": "1990-01-01",
            "passport": "E1234567",
            "email": "john.doe@example.com",
            "phoneType": "mobile",
            "phoneNumber": "91234567",
            "relationship": "main"
        }
    ]

    mock_main_contact = {
        "id": "1",
        "title": "Mr",
        "firstName": "John",
        "lastName": "Doe",
        "nationality": "SG",
        "dateOfBirth": "1990-01-01",
        "passport": "E1234567",
        "email": "john.doe@example.com",
        "phoneType": "mobile",
        "phoneNumber": "91234567",
        "address": "123 Main St",
        "city": "Singapore",
        "zipCode": "123456",
        "countryCode": "SG"
    }

    # Create schema with purchase data
    import copy
    purchase_schema = copy.deepcopy(taxonomy_dict)
    purchase_schema["insureds"] = mock_insureds
    purchase_schema["mainContact"] = mock_main_contact

    print("\nMock purchase call (will fail without valid quoteId)...")
    result = purchase_insurance(
        schema=purchase_schema,
        quote_id="mock-quote-id",
        offer_id="mock-offer-id",
        product_code="SG_AXA_SCOOT_COMP",
        unit_price=17.6,
        currency="SGD",
        quantity=1,
        is_send_email=True
    )

    print(f"Success: {result.get('success')}")
    if result.get('success'):
        print("Purchase successful!")
        print(f"Purchase data: {result.get('purchase_data')}")
    else:
        print(f"Expected error (mock data): {result.get('error')}")


def run_all_tests():
    """Run all test functions"""
    print("=" * 60)
    print("Document Magic Agent Test Suite")
    print("=" * 60)

    # Run tests
    test_missing_fields_identification()
    test_extract_and_fill_profile()
    test_get_insurance_quote()
    test_purchase_insurance()

    print("\n" + "=" * 60)
    print("Test suite completed!")
    print("=" * 60)


if __name__ == "__main__":
    run_all_tests()
