"""
Complete END-TO-END test of the full pipeline
"""
import requests
import time

API_URL = "http://localhost:8000/chat"
TEST_USER = "e2e_test"

def send(msg, file=None):
    data = {"user_id": TEST_USER, "session_id": f"s_{TEST_USER}", "message": msg}
    files = None
    if file:
        with open(file, 'rb') as f:
            mime = 'image/png' if file.endswith('.png') else 'application/pdf'
            files = {'file': (file.split('/')[-1], f.read(), mime)}
    
    print(f"\n>>> {msg}" + (f" [+{file.split('/')[-1]}]" if file else ""))
    r = requests.post(API_URL, data=data, files=files)
    if r.status_code == 200:
        latest = r.json()['messages'][-1]['content']
        print(f"<<< {latest[:200]}{'...' if len(latest) > 200 else ''}")
        return 'Product A' in latest or 'Product B' in latest
    print(f"ERROR: {r.status_code}")
    return False

print("🧪 COMPLETE END-TO-END PIPELINE TEST\n")
send("Hi, I need insurance")
time.sleep(2)

print("\n📎 STEP 1: Upload itinerary")
send("Here's my itinerary", "/Users/ray/Desktop/hackdeez/backend/ai_backend/sample_data/sample_itineraries/Europe_Multi_City_Solo.pdf")
time.sleep(3)

print("\n📎 STEP 2: Upload passport")
send("Here's my passport", "/Users/ray/Desktop/hackdeez/backend/ai_backend/sample_data/sample_passport/sample2.png")
time.sleep(3)

print("\n📝 STEP 3: Provide contact (should trigger policy recs!)")
has_recs = send("My email is test@example.com, phone +65-1234-5678, I live at 10 Marina Blvd, Singapore 018980")
time.sleep(5)

if has_recs:
    print("\n✅ SUCCESS - COMPLETE PIPELINE WORKING!")
else:
    print("\n⚠️ Check logs for policy recommendations")
