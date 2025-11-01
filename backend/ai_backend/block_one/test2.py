import requests

url = "https://dev.api.ancileo.com/v1/travel/front/purchase"

headers = {
    "Content-Type": "application/json",
    "X-API-Key": "98608e5b-249f-420e-896c-199a08699fc1"  # replace with your API key
}

payload = {
    "market": "SG",
    "languageCode": "en",
    "channel": "white-label",
    "quoteId": "fc69bf68-c729-41c9-8012-93ed69a6628e",
    "purchaseOffers": [
        {
            "productType": "travel-insurance",
            "offerId": "f80dfc75-36e3-433a-b561-f182383cd342",
            "productCode": "SG_AXA_SCOOT_COMP",
            "unitPrice": 17.6,
            "currency": "SGD",
            "quantity": 1,
            "totalPrice": 17.6,
            "isSendEmail": True
        }
    ],
    "insureds": [
        {
            "id": "1",
            "title": "Mr",
            "firstName": "John",
            "lastName": "Doe",
            "nationality": "SG",
            "dateOfBirth": "2000-01-01",
            "passport": "123456",
            "email": "john.doe@gmail.com",
            "phoneType": "mobile",
            "phoneNumber": "081111111",
            "relationship": "main"
        }
    ],
    "mainContact": {
        "id": "1",
        "title": "Mr",
        "firstName": "John",
        "lastName": "Doe",
        "nationality": "SG",
        "dateOfBirth": "2000-01-01",
        "passport": "123456",
        "email": "john.doe@gmail.com",
        "phoneType": "mobile",
        "phoneNumber": "081111111",
        "address": "12 test test 12",
        "city": "SG",
        "zipCode": "12345",
        "countryCode": "SG"
    }
}

response = requests.post(url, json=payload, headers=headers)

print(response.status_code)
print(response.text)
