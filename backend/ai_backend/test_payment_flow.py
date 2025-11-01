"""
Test the payment flow (with mocked payment service for now)
Since the Go payment service requires MySQL database which isn't running,
this test validates the payment flow with a mock payment completion.
"""
import sys
import os
from dotenv import load_dotenv

load_dotenv()
sys.path.append('/Users/ray/Desktop/hackdeez/backend/ai_backend')

from agents.Conversation_agent.tools import call_pricing_api, make_payment, call_purchase_api
from profile_manager import load_profile, save_profile

TEST_USER = "payment_test_user"

print("💳 TESTING COMPLETE PAYMENT FLOW")
print("="*80)

# Setup: Create test profile with required fields
print("\n🔧 SETUP: Creating test profile...")
print("-"*80)
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
        "firstName": "John",
        "lastName": "Doe",
        "nationality": "SG",
        "dateOfBirth": "1990-05-15",
        "passport": "X1234567A",
        "email": "john.doe@example.com",
        "phoneType": "mobile",
        "phoneNumber": "+6591234567",
        "relationship": "main"
    }],
    "mainContact": {
        "id": "1",
        "title": "Mr",
        "firstName": "John",
        "lastName": "Doe",
        "nationality": "SG",
        "dateOfBirth": "1990-05-15",
        "passport": "X1234567A",
        "email": "john.doe@example.com",
        "phoneType": "mobile",
        "phoneNumber": "+6591234567",
        "address": "123 Orchard Road",
        "city": "Singapore",
        "zipCode": "238858",
        "countryCode": "SG"
    }
})
save_profile(TEST_USER, profile)
print("✅ Test profile created")

# Step 1: Get pricing quote
print("\n📊 STEP 1: Getting pricing quote...")
print("-"*80)
quote_result = call_pricing_api(TEST_USER)

if quote_result.get("error"):
    print(f"❌ Error: {quote_result}")
    sys.exit(1)

first_offer = quote_result['offers'][0]
price_sgd = first_offer.get('unitPrice')
price_cents = int(price_sgd * 100)  # Convert to cents

print(f"✅ Quote received:")
print(f"   Quote ID: {quote_result.get('quoteId')}")
print(f"   Offer ID: {first_offer.get('id')}")
print(f"   Price: ${price_sgd} SGD = {price_cents} cents")

# Step 2: Process payment
print("\n💰 STEP 2: Processing payment...")
print("-"*80)
payment_result = make_payment(TEST_USER, price_cents, "Travel Insurance Payment")

if payment_result.get("error"):
    print(f"❌ Payment Error: {payment_result}")
    print(f"\n⚠️  NOTE: Payment service requires MySQL database on port 3306")
    print(f"   For now, we're testing with mocked payment completion")

    # Mock the payment manually for testing
    print(f"\n🔧 Manually mocking payment completion...")
    profile = load_profile(TEST_USER)
    profile["payment_status"] = "completed"
    profile["payment_id"] = f"mock_payment_{TEST_USER}"
    profile["payment_amount"] = price_cents
    save_profile(TEST_USER, profile)
    print(f"✅ Payment mocked as completed")
else:
    print(f"✅ Payment processed:")
    print(f"   Payment ID: {payment_result.get('payment_id')}")
    print(f"   Amount: ${payment_result.get('amount')} {payment_result.get('currency')}")
    print(f"   Status: {payment_result.get('status')}")
    if payment_result.get('client_secret'):
        print(f"   Client Secret: {payment_result.get('client_secret')[:20]}...")

# Step 3: Complete purchase
print("\n🛒 STEP 3: Completing purchase...")
print("-"*80)
purchase_result = call_purchase_api(TEST_USER, payment_confirmed=True)

if purchase_result.get("error"):
    print(f"❌ Purchase Error: {purchase_result.get('message')}")
    if purchase_result.get('request_payload'):
        import json
        print(f"\n📋 Request payload sent:")
        print(json.dumps(purchase_result['request_payload'], indent=2))
    sys.exit(1)

print(f"\n✅ PURCHASE SUCCESSFUL!")
print(f"\n📜 Purchase Details:")
print(f"   Policy ID: {purchase_result.get('policyId')}")
print(f"   Quote ID: {purchase_result.get('quoteId')}")
print(f"   Email: {purchase_result.get('confirmationEmail')}")

if purchase_result.get('purchasedOffers'):
    offer = purchase_result['purchasedOffers'][0]
    print(f"\n📦 Purchased Offer:")
    print(f"   Product Code: {offer.get('productCode')}")
    print(f"   Price: ${offer.get('unitPrice')} {offer.get('currency')}")
    print(f"   Cover Dates: {offer.get('coverDates', {}).get('from')} to {offer.get('coverDates', {}).get('to')}")

print("\n" + "="*80)
print("🎉 COMPLETE FLOW WORKS: PRICING → PAYMENT → PURCHASE")
print("\n📝 NOTES:")
print("   - Payment is currently MOCKED (auto-completed)")
print("   - Full payment integration requires:")
print("     1. Start MySQL database on port 3306")
print("     2. Run Go payment service: cd insuredeez-backend && go run cmd/insuredeez/main.go")
print("     3. Update make_payment to use webhook-based status checking")
