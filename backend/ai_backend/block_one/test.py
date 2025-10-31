import requests

url = "https://dev.api.ancileo.com/v1/travel/front/pricing"

headers = {
    "Content-Type": "application/json",
    "x-api-key": "98608e5b-249f-420e-896c-199a08699fc1"
}

payload = {
    "market": "SG",
    "languageCode": "en",
    "channel": "white-label",
    "deviceType": "DESKTOP",
    "context": {
        "tripType": "ST",   # ST = Single Trip, RT = Round Trip
        "departureDate": "2025-11-01",
        "returnDate": "2025-11-15",
        "departureCountry": "SG",
        "arrivalCountry": "CN",
        "adultsCount": 1,
        "childrenCount": 0
    }
}

response = requests.post(url, headers=headers, json=payload)

print("Status Code:", response.status_code)
print("Response JSON:", response.json())
