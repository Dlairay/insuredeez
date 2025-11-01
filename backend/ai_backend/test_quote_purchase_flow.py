"""
Test the complete quote → purchase flow using the agent tools
"""
import sys
import os
from dotenv import load_dotenv

# Load environment variables FIRST
load_dotenv()

sys.path.append('/Users/ray/Desktop/hackdeez/backend/ai_backend')

from agents.Conversation_agent.tools import call_pricing_api, call_purchase_api, make_payment
from profile_manager import load_profile, save_profile

TEST_USER = "quote_test_user"

print("🧪 TESTING COMPLETE QUOTE → PURCHASE FLOW\n")
print("="*80)

# Step 1: Create a complete profile
print("\n📋 STEP 1: Setting up complete user profile...")
profile = load_profile(TEST_USER)
profile.update({
    "tripType": "ST",
    "departureDate": "2026-01-15",
    "returnDate": "2026-02-12",
    "departureCountry": "SG",
    "arrivalCountry": "FR",
    "adultsCount": 1,
    "childrenCount": 0,
    "insureds": [{
        "id": "1",
        "title": "Mr",
        "firstName": "ALVIN",
        "lastName": "CHUA",
        "nationality": "SG",
        "dateOfBirth": "1978-05-26",
        "passport": "X1000458A",
        "email": "alvin.test@example.com",
        "phoneType": "mobile",
        "phoneNumber": "+6512345678",
        "relationship": "main"
    }],
    "mainContact": {
        "id": "1",
        "title": "Mr",
        "firstName": "ALVIN",
        "lastName": "CHUA",
        "nationality": "SG",
        "dateOfBirth": "1978-05-26",
        "passport": "X1000458A",
        "email": "alvin.test@example.com",
        "phoneType": "mobile",
        "phoneNumber": "+6512345678",
        "address": "123 Orchard Road",
        "city": "Singapore",
        "zipCode": "238858",
        "countryCode": "SG"
    }
})
save_profile(TEST_USER, profile)
print("✅ Profile created with complete trip + personal + contact info")

# Step 2: Get pricing quote
print("\n\n💰 STEP 2: Getting pricing quote...")
print("-"*80)
quote_result = call_pricing_api(TEST_USER)

if quote_result.get("error"):
    print(f"❌ Pricing API Error: {quote_result}")
    sys.exit(1)

print(f"✅ Quote received!")
print(f"   Quote ID: {quote_result.get('quoteId')}")
print(f"   Number of offers: {len(quote_result.get('offers', []))}")

if quote_result.get('offers'):
    first_offer = quote_result['offers'][0]
    print(f"   Offer ID: {first_offer.get('id')}")
    print(f"   Product: {first_offer.get('productCode')}")
    print(f"   Price: ${first_offer.get('unitPrice')} {first_offer.get('currency')}")

# Step 3: Process payment
print("\n\n💳 STEP 3: Processing payment...")
print("-"*80)
amount_cents = int(first_offer.get('unitPrice', 33.33) * 100)  # Convert to cents
print(f"Amount: ${amount_cents/100:.2f} ({amount_cents} cents)")

payment_result = make_payment(TEST_USER, amount_cents, "Travel Insurance Premium")

if not payment_result.get("success"):
    print(f"❌ Payment Error: {payment_result}")
    sys.exit(1)

print(f"✅ Payment processed!")
print(f"   Payment ID: {payment_result.get('paymentId')}")

# Mark payment as completed in profile (simulate successful payment)
profile = load_profile(TEST_USER)
profile["payment_status"] = "completed"
save_profile(TEST_USER, profile)

# Step 4: Complete purchase
print("\n\n🛒 STEP 4: Completing insurance purchase...")
print("-"*80)
purchase_result = call_purchase_api(TEST_USER, payment_confirmed=True)

if purchase_result.get("error"):
    print(f"❌ Purchase API Error: {purchase_result}")
    if purchase_result.get('request_payload'):
        import json
        print(f"\nRequest payload:")
        print(json.dumps(purchase_result['request_payload'], indent=2))
    sys.exit(1)

print(f"✅ Purchase completed!")
print(f"   Policy ID: {purchase_result.get('policyId')}")
print(f"   Quote ID: {purchase_result.get('quoteId')}")
print(f"   Confirmation Email: {purchase_result.get('confirmationEmail')}")

print("\n" + "="*80)
print("🎉 COMPLETE FLOW SUCCESSFUL!")
print("\nFlow Summary:")
print("1. ✅ Created complete user profile")
print("2. ✅ Retrieved pricing quote from Ancileo API")
print("3. ✅ Processed payment")
print("4. ✅ Completed insurance purchase")
print(f"\nFinal Policy ID: {purchase_result.get('policyId')}")
