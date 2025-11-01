# File Upload Guide - Travel Insurance Chatbot

## How to Use the Terminal Chat Client

### 1. Start the FastAPI Server
```bash
python app.py
# Server runs on http://localhost:8000
```

### 2. Start the Terminal Client (in another terminal)
```bash
python terminal_chat_client.py
```

### 3. Upload Files During Chat

The terminal client supports uploading files like passport images, itinerary PDFs, etc.

**Command Format:**
```
/upload <filepath> <optional description>
```

**Examples:**

```bash
# Upload passport photo
You: /upload ~/Desktop/passport.jpg Here is my passport

# Upload itinerary PDF
You: /upload ~/Documents/bali_trip.pdf My travel itinerary for Bali

# Upload ID card
You: /upload ./id_card.png My Singapore ID card

# Just upload without description
You: /upload ./documents/flight_booking.pdf
```

**Supported File Types:**
- Images: `.jpg`, `.jpeg`, `.png`, `.gif`
- Documents: `.pdf`, `.txt`
- The API accepts any file type, but document_magic_agent works best with images and PDFs

---

## How File Upload Works (Technical Details)

### What the API Expects

The `/chat` endpoint accepts **multipart/form-data** with these fields:

```python
POST /chat
Content-Type: multipart/form-data

Fields:
- user_id: str (required)
- message: str (required)
- session_id: str (optional)
- file: UploadFile (optional)
```

### NO Base64 Encoding Needed!

**Important:** The API accepts **raw file uploads**, NOT base64 encoded strings.

The terminal client handles this automatically using `requests.post()` with `files` parameter:

```python
files = {
    'file': (filename, open(filepath, 'rb'), mime_type)
}
response = requests.post(CHAT_ENDPOINT, data=form_data, files=files)
```

### Behind the Scenes

When you upload a file:

1. **Terminal Client** → Reads file as binary and sends via multipart/form-data
2. **FastAPI** → Receives as `UploadFile`, reads bytes
3. **Google ADK** → Converts bytes to `types.Part.from_bytes()`
4. **Gemini Model** → Processes the file (image/PDF) using vision capabilities
5. **document_magic_agent** → Extracts trip details, passport info, etc.

---

## Testing File Uploads

### Sample Test Files

Create test files to upload:

```bash
# Create a sample text file
echo "Trip to Bali, Indonesia
Departure: 2025-12-01
Return: 2025-12-15
2 adults" > ~/Desktop/test_itinerary.txt

# Upload it
You: /upload ~/Desktop/test_itinerary.txt My trip details
```

### Example Chat Session

```
You: Hello, I need travel insurance
🤖 Assistant: Hello! I'd be happy to help you with travel insurance...

You: /upload ~/Desktop/passport.jpg Here is my passport
📎 Uploading file: passport.jpg (image/jpeg)
🤖 Assistant: I've extracted your information from the passport...

You: /upload ~/Desktop/itinerary.pdf My Bali trip itinerary
📎 Uploading file: itinerary.pdf (application/pdf)
🤖 Assistant: I see you're traveling to Bali from Dec 1-15, 2025...

You: What insurance do you recommend?
🤖 Assistant: Based on your itinerary showing surfing and diving activities...
```

---

## Alternative: Using cURL

If you want to test the API directly with cURL:

```bash
# Text message only
curl -X POST http://localhost:8000/chat \
  -F "user_id=test_user" \
  -F "message=I want travel insurance"

# With file upload
curl -X POST http://localhost:8000/chat \
  -F "user_id=test_user" \
  -F "message=Here is my passport" \
  -F "file=@/path/to/passport.jpg"
```

---

## Alternative: Using Python Requests

```python
import requests

# Send message with file
response = requests.post(
    "http://localhost:8000/chat",
    data={
        "user_id": "test_user",
        "session_id": "session_001",
        "message": "Here is my passport photo"
    },
    files={
        "file": ("passport.jpg", open("passport.jpg", "rb"), "image/jpeg")
    }
)

print(response.json()["messages"])
```

---

## If You Need Base64 (Reference Only)

**Note:** The API doesn't use base64, but here's how to encode if needed for other purposes:

```python
import base64

# Encode file to base64
with open("passport.jpg", "rb") as f:
    base64_string = base64.b64encode(f.read()).decode('utf-8')

print(base64_string)  # iVBORw0KGgoAAAANS...

# Decode back to bytes
file_bytes = base64.b64decode(base64_string)
```

But again, **you don't need this for the chat API** - just use the `/upload` command in the terminal client!

---

## Troubleshooting

**"Cannot connect to server"**
- Make sure `python app.py` is running
- Check server is on `http://localhost:8000`

**"File not found"**
- Use full path: `/Users/ray/Desktop/passport.jpg`
- Or use `~`: `~/Desktop/passport.jpg`
- Or relative path: `./passport.jpg`

**"No response from assistant"**
- Check server logs for errors
- Ensure GEMINI_API_KEY is set in .env
- File might be too large (Google ADK has size limits)

---

## Quick Start Example

Terminal 1:
```bash
cd /Users/ray/Desktop/hackdeez/backend/ai_backend
python app.py
```

Terminal 2:
```bash
cd /Users/ray/Desktop/hackdeez/backend/ai_backend
python terminal_chat_client.py

# Follow prompts
Enter your user ID: john_doe

You: Hello! I want to buy travel insurance for my Bali trip
You: /upload ~/Desktop/bali_itinerary.pdf Here is my trip itinerary
You: What do you recommend?
```

That's it! 🎉
