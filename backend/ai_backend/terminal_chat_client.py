"""
Terminal UI Client for Travel Insurance Chatbot
Sends messages and files to the FastAPI chat endpoint

Usage:
  python terminal_chat_client.py

Commands:
  /upload <filepath> <description>  - Upload a file (passport, itinerary, etc.)
  /clear                            - Clear session history
  /quit or /exit                    - Exit the client
  /help                             - Show this help message

Example:
  You: I want to buy travel insurance
  You: /upload ~/Desktop/passport.jpg Here is my passport photo
  You: /upload ~/Desktop/itinerary.pdf My trip itinerary
"""

import requests
import os
import sys
from pathlib import Path
from typing import Optional

# ============================================================================
# CONFIGURATION
# ============================================================================

API_URL = "http://localhost:8000"
CHAT_ENDPOINT = f"{API_URL}/chat"
CLEAR_ENDPOINT = f"{API_URL}/session"

# ANSI color codes for terminal
class Colors:
    USER = '\033[94m'      # Blue
    ASSISTANT = '\033[92m' # Green
    SYSTEM = '\033[93m'    # Yellow
    ERROR = '\033[91m'     # Red
    RESET = '\033[0m'      # Reset
    BOLD = '\033[1m'       # Bold

# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def print_colored(text: str, color: str = Colors.RESET):
    """Print colored text to terminal"""
    print(f"{color}{text}{Colors.RESET}")


def print_message(role: str, content: str):
    """Print a formatted message"""
    if role == "user":
        print_colored(f"\n💬 You: {content}", Colors.USER)
    elif role == "assistant":
        print_colored(f"\n🤖 Assistant: {content}", Colors.ASSISTANT)
    else:
        print_colored(f"\n{role}: {content}", Colors.SYSTEM)


def print_banner():
    """Print welcome banner"""
    print_colored("\n" + "=" * 80, Colors.BOLD)
    print_colored("🛡️  Travel Insurance Chatbot - Terminal Client", Colors.BOLD)
    print_colored("=" * 80, Colors.RESET)
    print_colored("\nType '/help' for commands, '/quit' to exit\n", Colors.SYSTEM)


def print_help():
    """Print help message"""
    help_text = """
📖 Available Commands:

  /upload <filepath> <description>   Upload a file with optional description
                                     Example: /upload ~/passport.jpg My passport

  /clear                             Clear current session (start fresh)

  /quit or /exit                     Exit the client

  /help                              Show this help message

💡 Tips:
  - Just type normally to chat with the assistant
  - Upload passport, ID, or itinerary PDFs/images using /upload
  - The assistant will extract information from your documents
  - All files are sent directly (not base64 encoded)
"""
    print_colored(help_text, Colors.SYSTEM)


def send_message(
    user_id: str,
    session_id: str,
    message: str,
    file_path: Optional[str] = None
) -> dict:
    """
    Send a message (and optionally a file) to the chat endpoint

    Args:
        user_id: User identifier
        session_id: Session identifier
        message: Text message
        file_path: Optional path to file to upload

    Returns:
        Response JSON from server
    """
    try:
        # Prepare form data
        data = {
            "user_id": user_id,
            "session_id": session_id,
            "message": message
        }

        files = None
        if file_path:
            # Expand ~ and resolve path
            file_path = os.path.expanduser(file_path)

            if not os.path.exists(file_path):
                print_colored(f"❌ Error: File not found: {file_path}", Colors.ERROR)
                return None

            # Determine MIME type
            ext = Path(file_path).suffix.lower()
            mime_types = {
                '.pdf': 'application/pdf',
                '.jpg': 'image/jpeg',
                '.jpeg': 'image/jpeg',
                '.png': 'image/png',
                '.gif': 'image/gif',
                '.txt': 'text/plain'
            }
            mime_type = mime_types.get(ext, 'application/octet-stream')

            # Open file
            files = {
                'file': (os.path.basename(file_path), open(file_path, 'rb'), mime_type)
            }

            print_colored(f"📎 Uploading file: {os.path.basename(file_path)} ({mime_type})", Colors.SYSTEM)

        # Send request
        response = requests.post(CHAT_ENDPOINT, data=data, files=files, timeout=120)

        # Close file if opened
        if files:
            files['file'][1].close()

        if response.status_code == 200:
            return response.json()
        else:
            print_colored(f"❌ Error: {response.status_code} - {response.text}", Colors.ERROR)
            return None

    except requests.exceptions.ConnectionError:
        print_colored(f"❌ Error: Cannot connect to server at {API_URL}", Colors.ERROR)
        print_colored("   Make sure the FastAPI server is running: python app.py", Colors.SYSTEM)
        return None
    except Exception as e:
        print_colored(f"❌ Error: {e}", Colors.ERROR)
        return None


def clear_session(user_id: str, session_id: str):
    """Clear the current session"""
    try:
        response = requests.delete(f"{CLEAR_ENDPOINT}/{user_id}/{session_id}", timeout=10)
        if response.status_code == 200:
            print_colored("✅ Session cleared! Starting fresh conversation.", Colors.SYSTEM)
        else:
            print_colored(f"❌ Error clearing session: {response.text}", Colors.ERROR)
    except Exception as e:
        print_colored(f"❌ Error: {e}", Colors.ERROR)


# ============================================================================
# MAIN CHAT LOOP
# ============================================================================

def main():
    """Main terminal chat interface"""

    print_banner()

    # Get user info
    user_id = input("Enter your user ID (or press Enter for 'test_user'): ").strip()
    if not user_id:
        user_id = "test_user"

    session_id = f"session_{user_id}"
    print_colored(f"\n✅ Connected as: {user_id}", Colors.SYSTEM)
    print_colored(f"📋 Session ID: {session_id}\n", Colors.SYSTEM)

    # Chat loop
    while True:
        try:
            # Get user input
            user_input = input(f"{Colors.BOLD}You: {Colors.RESET}").strip()

            if not user_input:
                continue

            # Handle commands
            if user_input.lower() in ['/quit', '/exit', '/q']:
                print_colored("\n👋 Goodbye! Thanks for using the Travel Insurance Chatbot.", Colors.SYSTEM)
                break

            elif user_input.lower() == '/help':
                print_help()
                continue

            elif user_input.lower() == '/clear':
                clear_session(user_id, session_id)
                continue

            elif user_input.lower().startswith('/upload'):
                # Parse upload command: /upload <filepath> <description>
                parts = user_input.split(maxsplit=2)

                if len(parts) < 2:
                    print_colored("❌ Usage: /upload <filepath> [description]", Colors.ERROR)
                    print_colored("   Example: /upload ~/passport.jpg Here is my passport", Colors.SYSTEM)
                    continue

                file_path = parts[1]
                description = parts[2] if len(parts) > 2 else "Uploaded document"

                # Send with file
                response = send_message(user_id, session_id, description, file_path)

            else:
                # Regular text message
                response = send_message(user_id, session_id, user_input)

            # Display response
            if response:
                # Print the latest assistant message
                messages = response.get('messages', [])
                if messages:
                    # Show only the latest assistant response
                    for msg in reversed(messages):
                        if msg['role'] == 'assistant':
                            print_message('assistant', msg['content'])
                            break
                else:
                    print_colored("⚠️  No response from assistant", Colors.SYSTEM)

            print()  # Spacing

        except KeyboardInterrupt:
            print_colored("\n\n👋 Chat interrupted. Goodbye!", Colors.SYSTEM)
            break

        except Exception as e:
            print_colored(f"\n❌ Error: {e}", Colors.ERROR)
            print_colored("Type '/quit' to exit or continue chatting\n", Colors.SYSTEM)


if __name__ == "__main__":
    main()
