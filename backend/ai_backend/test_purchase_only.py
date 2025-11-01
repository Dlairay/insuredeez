"""
Test purchase API directly (skip payment for now)
"""
import sys
import os
from dotenv import load_dotenv

load_dotenv()
sys.path.append('/Users/ray/Desktop/hackdeez/backend/ai_backend')

from agents.Conversation_agent.tools import call_pricing_api, call_purchase_api
from profile_manager import load_profile, save_profile

TEST_USER = "quote_test_user"

print("🧪 TESTING PRICING → PURCHASE FLOW (Skip Payment)\n")
print("="*80)

# Get pricing quote
print("\n💰 Getting pricing quote...")
quote_result = call_pricing_api(TEST_USER)

if quote_result.get("error"):
    print(f"❌ Error: {quote_result}")
    sys.exit(1)

first_offer = quote_result['offers'][0]
print(f"✅ Quote: ${first_offer.get('unitPrice')} {first_offer.get('currency')}")
print(f"   Quote ID: {quote_result.get('quoteId')}")
print(f"   Offer ID: {first_offer.get('id')}")

# Simulate payment completed (skip actual payment gateway)
print("\n💳 Simulating payment completed...")
profile = load_profile(TEST_USER)
profile["payment_status"] = "completed"
save_profile(TEST_USER, profile)
print("✅ Payment status set to 'completed'")

# Complete purchase
print("\n🛒 Calling purchase API...")
print("-"*80)
purchase_result = call_purchase_api(TEST_USER, payment_confirmed=True)

if purchase_result.get("error"):
    print(f"\n❌ Purchase Error: {purchase_result.get('message')}")
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
print("🎉 PRICING → PURCHASE FLOW WORKS!")
