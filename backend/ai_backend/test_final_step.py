"""
Test final step - provide contact info to trigger policy recommendations
Assumes profile already has trip + personal details
"""
import requests

API_URL = "http://localhost:8000/chat"
# Use the same user from previous test - should have trip + personal info already
TEST_USER = "complete_pipeline_user"

def send_message(message):
    data = {
        "user_id": TEST_USER,
        "session_id": f"session_{TEST_USER}",
        "message": message
    }

    print(f"\n>>> User: {message}")
    response = requests.post(API_URL, data=data)

    if response.status_code == 200:
        result = response.json()
        messages = result.get('messages', [])
        if messages:
            latest = messages[-1]
            if latest['role'] == 'assistant':
                print(f"\n<<< Assistant:")
                print(latest['content'])

                if 'Product A' in latest['content'] or 'Product B' in latest['content'] or 'Product C' in latest['content']:
                    print("\n✅ SUCCESS - POLICY RECOMMENDATIONS SHOWN!")
                    return True
    else:
        print(f"ERROR: {response.status_code} - {response.text}")
    
    return False

print("🧪 TESTING FINAL STEP - Provide contact info to complete profile")
print("="*80)

success = send_message("My email is alvin.chua@email.com, phone is +65 9123 4567, and I live at 123 Orchard Road, Singapore 238858")

if success:
    print("\n✅ COMPLETE PIPELINE WORKING!")
else:
    print("\n❌ Policy recommendations not shown - check logs")
