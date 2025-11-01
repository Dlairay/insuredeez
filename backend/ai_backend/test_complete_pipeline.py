"""
Test complete pipeline - user must provide ALL info before seeing recommendations
"""
import requests
import time

API_URL = "http://localhost:8000/chat"
TEST_USER = "complete_pipeline_user"

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
    print(f">>> User: {message}")
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

                # Check for policy recommendations
                if 'Product A' in latest['content'] or 'Product B' in latest['content']:
                    print("\n✅ POLICY RECOMMENDATIONS SHOWN!")
                if 'still missing' in latest['content'].lower() or 'need' in latest['content'].lower():
                    print("\n⚠️  Agent asking for more information")
        return result
    else:
        print(f"ERROR: {response.status_code} - {response.text}")
        return None

print("🧪 TESTING COMPLETE PIPELINE - Must collect ALL info before recommendations")
print("="*80)

# Step 1: Greeting
send_message("Hi, I need travel insurance")
time.sleep(2)

# Step 2: Upload itinerary (has trip details but missing personal/contact info)
print("\n\n📎 STEP 2: UPLOAD ITINERARY")
send_message(
    "Here is my trip itinerary",
    "/Users/ray/Desktop/hackdeez/backend/ai_backend/sample_data/sample_itineraries/Europe_Multi_City_Solo.pdf"
)
time.sleep(3)
print("\n⚠️  Expected: Should ask for personal details (passport) and contact info")
print("⚠️  Should NOT show policy recommendations yet!")

# Step 3: Upload passport (has personal details but still missing contact info)
print("\n\n📎 STEP 3: UPLOAD PASSPORT")
send_message(
    "Here is my passport",
    "/Users/ray/Desktop/hackdeez/backend/ai_backend/sample_data/sample_passport/sample2.png"
)
time.sleep(3)
print("\n⚠️  Expected: Should ask for contact info (email, phone, address)")
print("⚠️  Should NOT show policy recommendations yet!")

# Step 4: Provide contact information (completes the profile)
print("\n\n📝 STEP 4: PROVIDE CONTACT INFO")
send_message(
    "My email is alvin.chua@email.com, phone is +65 9123 4567, and I live at 123 Orchard Road, Singapore 238858"
)
time.sleep(5)
print("\n✅ Expected: Profile should be COMPLETE - should AUTOMATICALLY show policy recommendations!")

print("\n\n🏁 TEST COMPLETE")
