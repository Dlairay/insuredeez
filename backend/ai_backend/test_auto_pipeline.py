"""
Test automatic policy recommendation triggering after document upload
"""
import requests
import time

API_URL = "http://localhost:8000/chat"
TEST_USER = "pipeline_test_user"

def send_message(message, file_path=None):
    """Send a message to the chat API"""
    data = {
        "user_id": TEST_USER,
        "session_id": f"session_{TEST_USER}",
        "message": message
    }

    files = None
    if file_path:
        with open(file_path, 'rb') as f:
            mime = 'image/png' if file_path.endswith('.png') else 'application/pdf'
            files = {'file': (file_path.split('/')[-1], f.read(), mime)}

    print(f"\n{'='*80}")
    print(f">>> Sending: {message}")
    if file_path:
        print(f">>> With file: {file_path.split('/')[-1]}")

    response = requests.post(API_URL, data=data, files=files)

    if response.status_code == 200:
        result = response.json()
        messages = result.get('messages', [])
        if messages:
            latest = messages[-1]
            if latest['role'] == 'assistant':
                print(f"\n<<< Assistant:")
                print(latest['content'])

                # Check if policy recommendations are in the response
                if 'Product A' in latest['content'] or 'Product B' in latest['content'] or 'Product C' in latest['content']:
                    print("\n✅ POLICY RECOMMENDATIONS DETECTED!")
                if 'insurance option' in latest['content'].lower() or 'insurance card' in latest['content'].lower():
                    print("\n✅ INSURANCE CARDS MENTIONED!")
        return result
    else:
        print(f"ERROR: {response.status_code} - {response.text}")
        return None

print("🧪 TESTING AUTOMATIC POLICY RECOMMENDATION PIPELINE")
print("="*80)

# Step 1: Greeting
send_message("Hi, I need travel insurance")
time.sleep(2)

# Step 2: Upload itinerary first (has trip details)
print("\n\n📎 UPLOADING ITINERARY (should trigger automatic policy recs)...")
send_message(
    "Here is my trip itinerary",
    "/Users/ray/Desktop/hackdeez/backend/ai_backend/sample_data/sample_itineraries/Europe_Multi_City_Solo.pdf"
)
time.sleep(3)

print("\n\n🏁 TEST COMPLETE - Check if policy recommendations were automatically triggered!")
