"""
Test the actual Ancileo pricing and purchase API flow
"""
import requests
import json
import os
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv("ANCILIEO_API_KEY")
if not API_KEY:
    print("❌ ANCILIEO_API_KEY not found in environment")
    exit(1)

PRICING_URL = "https://dev.api.ancileo.com/v1/travel/front/pricing"
PURCHASE_URL = "https://dev.api.ancileo.com/v1/travel/front/purchase"

print("🔍 Testing Ancileo API Flow\n")
print("="*80)

# Step 1: Call pricing API
print("\n📊 STEP 1: Calling Pricing API...")
print("-"*80)

pricing_payload = {
    "market": "SG",
    "languageCode": "en",
    "channel": "white-label",
    "deviceType": "DESKTOP",
    "context": {
        "tripType": "ST",
        "departureDate": "2026-01-15",
        "returnDate": "2026-02-12",
        "departureCountry": "SG",
        "arrivalCountry": "FR",
        "adultsCount": 1,
        "childrenCount": 0
    }
}

print("Payload:")
print(json.dumps(pricing_payload, indent=2))

headers = {
    "Content-Type": "application/json",
    "x-api-key": API_KEY
}

pricing_response = requests.post(PRICING_URL, json=pricing_payload, headers=headers)

print(f"\nStatus: {pricing_response.status_code}")

if pricing_response.status_code == 200:
    pricing_data = pricing_response.json()
    print("\n✅ Pricing API Response:")
    print(json.dumps(pricing_data, indent=2))
    
    # Extract key fields for purchase
    print("\n📋 KEY FIELDS FOR PURCHASE API:")
    print("-"*80)
    quote_id = pricing_data.get('id')
    print(f"Quote ID: {quote_id}")
    
    if 'offerCategories' in pricing_data:
        offers = pricing_data['offerCategories'][0]['offers']
        if offers:
            first_offer = offers[0]
            print(f"Offer ID: {first_offer.get('id')}")
            print(f"Product Code: {first_offer.get('productCode')}")
            print(f"Unit Price: {first_offer.get('unitPrice')}")
            print(f"Currency: {first_offer.get('priceBreakdown', {}).get('currency', 'SGD')}")
            
            # Step 2: Call purchase API with extracted data
            print("\n\n💳 STEP 2: Calling Purchase API...")
            print("-"*80)
            
            purchase_payload = {
                "market": "SG",
                "languageCode": "en",
                "channel": "white-label",
                "quoteId": quote_id,
                "purchaseOffers": [{
                    "productType": "travel-insurance",
                    "offerId": first_offer.get('id'),
                    "productCode": first_offer.get('productCode'),
                    "unitPrice": first_offer.get('unitPrice'),
                    "currency": first_offer.get('currency', 'SGD'),
                    "quantity": 1,
                    "totalPrice": first_offer.get('unitPrice'),
                    "isSendEmail": True
                }],
                "insureds": [{
                    "id": "1",
                    "title": "Mr",
                    "firstName": "ALVIN",
                    "lastName": "CHUA WEE TEE",
                    "nationality": "SG",
                    "dateOfBirth": "1978-05-26",
                    "passport": "X1000458A",
                    "email": "test@example.com",
                    "phoneType": "mobile",
                    "phoneNumber": "+6512345678",
                    "relationship": "main"
                }],
                "mainContact": {
                    "id": "1",
                    "title": "Mr",
                    "firstName": "ALVIN",
                    "lastName": "CHUA WEE TEE",
                    "nationality": "SG",
                    "dateOfBirth": "1978-05-26",
                    "passport": "X1000458A",
                    "email": "test@example.com",
                    "phoneType": "mobile",
                    "phoneNumber": "+6512345678",
                    "address": "123 Orchard Road",
                    "city": "Singapore",
                    "zipCode": "238858",
                    "countryCode": "SG"
                }
            }
            
            print("Payload:")
            print(json.dumps(purchase_payload, indent=2))
            
            purchase_headers = {
                "Content-Type": "application/json",
                "X-API-Key": API_KEY
            }
            
            purchase_response = requests.post(PURCHASE_URL, json=purchase_payload, headers=purchase_headers)
            
            print(f"\nStatus: {purchase_response.status_code}")
            
            if purchase_response.status_code == 200:
                purchase_data = purchase_response.json()
                print("\n✅ Purchase API Response:")
                print(json.dumps(purchase_data, indent=2))
            else:
                print(f"\n❌ Purchase API Error:")
                print(purchase_response.text)
else:
    print(f"\n❌ Pricing API Error:")
    print(pricing_response.text)

print("\n" + "="*80)
print("🏁 Test Complete")
