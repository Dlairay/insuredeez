"""
Test the terminal chat flow programmatically
"""
import requests
import time

API_URL = "http://localhost:8000/chat"
TEST_USER = "test_claude_agent"

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
        return result
    else:
        print(f"ERROR: {response.status_code} - {response.text}")
        return None

# Test flow
print("\n🧪 TESTING FULL PIPELINE")
print("="*80)

# Step 1: Initial greeting
send_message("Hi, I need travel insurance")
time.sleep(1)

# Step 2: Upload passport
print("\n\n📎 UPLOADING PASSPORT...")
send_message(
    "Here is my passport",
    "/Users/ray/Desktop/hackdeez/backend/ai_backend/sample_data/sample_passport/sample2.png"
)
time.sleep(2)

# Step 3: Upload itinerary
print("\n\n📎 UPLOADING ITINERARY...")
send_message(
    "Here is my trip itinerary",
    "/Users/ray/Desktop/hackdeez/backend/ai_backend/sample_data/sample_itineraries/Europe_Multi_City_Solo.pdf"
)
time.sleep(3)

# Step 4: Check artifact was created
import os
artifact_path = f"/Users/ray/Desktop/hackdeez/backend/ai_backend/agents/artifacts/user_{TEST_USER}_profile.py"
print(f"\n\n📁 CHECKING ARTIFACT: {artifact_path}")
if os.path.exists(artifact_path):
    print(f"✅ Artifact exists!")
    with open(artifact_path, 'r') as f:
        content = f.read()
        # Show first 50 lines
        lines = content.split('\n')[:50]
        print('\n'.join(lines))
else:
    print(f"❌ Artifact NOT found!")

print("\n\n🏁 TEST COMPLETE")
