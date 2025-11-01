"""
Simple JSON File Storage
Each user gets their own JSON file: {user_id}_profile.json
"""

import json
import os
from pathlib import Path
from typing import Dict, Optional, List
from datetime import datetime


class JSONStorage:
    """
    Simple file-based storage for user profiles.
    Each user = one JSON file with all their data.
    """

    def __init__(self, storage_dir: str = "user_data"):
        """
        Initialize JSON storage

        Args:
            storage_dir: Directory to store user JSON files
        """
        # Create storage directory in ai_backend/user_data/
        self.storage_dir = Path(__file__).parent.parent / storage_dir
        self.storage_dir.mkdir(exist_ok=True)
        print(f"[JSONStorage] Using directory: {self.storage_dir}")

    def _get_file_path(self, user_id: str) -> Path:
        """Get file path for user"""
        return self.storage_dir / f"{user_id}_profile.json"

    def get_user_profile(self, user_id: str) -> Optional[Dict]:
        """
        Load user profile from JSON file

        Args:
            user_id: User identifier

        Returns:
            User profile dict or None if doesn't exist
        """
        file_path = self._get_file_path(user_id)

        if not file_path.exists():
            return None

        try:
            with open(file_path, 'r') as f:
                profile = json.load(f)
            return profile
        except Exception as e:
            print(f"[JSONStorage] Error loading {user_id}: {e}")
            return None

    def save_user_profile(self, user_id: str, profile: Dict):
        """
        Save user profile to JSON file

        Args:
            user_id: User identifier
            profile: Complete user profile dictionary
        """
        file_path = self._get_file_path(user_id)

        # Add metadata
        profile['user_id'] = user_id
        profile['last_updated'] = datetime.utcnow().isoformat()

        try:
            with open(file_path, 'w') as f:
                json.dump(profile, f, indent=2)
            print(f"[JSONStorage] Saved profile for {user_id}")
        except Exception as e:
            print(f"[JSONStorage] Error saving {user_id}: {e}")
            raise

    def create_or_update_profile(self, user_id: str, updates: Dict) -> Dict:
        """
        Create new profile or update existing one

        Args:
            user_id: User identifier
            updates: Dictionary of updates to apply

        Returns:
            Updated profile
        """
        # Load existing or create new
        profile = self.get_user_profile(user_id)

        if profile is None:
            # New user
            profile = {
                "user_id": user_id,
                "created_at": datetime.utcnow().isoformat(),
                "conversation_history": [],
                "coverage_needs": [],
                "trip_summary": {},
                "context": {},
                "metadata": {}
            }
            print(f"[JSONStorage] Creating new profile for {user_id}")

        # Apply updates
        for key, value in updates.items():
            if key == "conversation_history" and isinstance(value, list):
                # Append to conversation history
                profile["conversation_history"].extend(value)
            elif key == "coverage_needs" and isinstance(value, list):
                # Replace coverage needs
                profile["coverage_needs"] = value
            else:
                # Update field
                profile[key] = value

        # Save
        self.save_user_profile(user_id, profile)

        return profile

    def add_message(self, user_id: str, role: str, content: str, metadata: Optional[Dict] = None):
        """
        Add a message to user's conversation history

        Args:
            user_id: User identifier
            role: "user" or "assistant"
            content: Message content
            metadata: Optional metadata
        """
        message = {
            "role": role,
            "content": content,
            "timestamp": datetime.utcnow().isoformat(),
            "metadata": metadata or {}
        }

        profile = self.get_user_profile(user_id)

        if profile is None:
            profile = {
                "user_id": user_id,
                "created_at": datetime.utcnow().isoformat(),
                "conversation_history": [message],
                "coverage_needs": [],
                "trip_summary": {},
                "context": {},
                "metadata": {}
            }
        else:
            profile["conversation_history"].append(message)

        self.save_user_profile(user_id, profile)

    def get_conversation_history(self, user_id: str) -> List[Dict]:
        """
        Get user's conversation history

        Args:
            user_id: User identifier

        Returns:
            List of messages
        """
        profile = self.get_user_profile(user_id)

        if profile is None:
            return []

        return profile.get("conversation_history", [])

    def update_context(self, user_id: str, context_updates: Dict):
        """
        Update user's context

        Args:
            user_id: User identifier
            context_updates: Dictionary of context updates
        """
        profile = self.get_user_profile(user_id)

        if profile is None:
            profile = {
                "user_id": user_id,
                "created_at": datetime.utcnow().isoformat(),
                "conversation_history": [],
                "coverage_needs": [],
                "trip_summary": {},
                "context": context_updates,
                "metadata": {}
            }
        else:
            # Update context
            if "context" not in profile:
                profile["context"] = {}
            profile["context"].update(context_updates)

        self.save_user_profile(user_id, profile)

    def clear_conversation_history(self, user_id: str):
        """
        Clear user's conversation history

        Args:
            user_id: User identifier
        """
        profile = self.get_user_profile(user_id)

        if profile is not None:
            profile["conversation_history"] = []
            self.save_user_profile(user_id, profile)

    def delete_user(self, user_id: str) -> bool:
        """
        Delete user's profile file

        Args:
            user_id: User identifier

        Returns:
            True if deleted, False if didn't exist
        """
        file_path = self._get_file_path(user_id)

        if file_path.exists():
            file_path.unlink()
            print(f"[JSONStorage] Deleted profile for {user_id}")
            return True

        return False

    def list_users(self) -> List[str]:
        """
        List all user IDs

        Returns:
            List of user IDs
        """
        user_ids = []

        for file_path in self.storage_dir.glob("*_profile.json"):
            user_id = file_path.stem.replace("_profile", "")
            user_ids.append(user_id)

        return user_ids

    def get_stats(self) -> Dict:
        """
        Get storage statistics

        Returns:
            Dictionary with stats
        """
        users = self.list_users()
        total_messages = 0
        total_needs = 0

        for user_id in users:
            profile = self.get_user_profile(user_id)
            if profile:
                total_messages += len(profile.get("conversation_history", []))
                total_needs += len(profile.get("coverage_needs", []))

        return {
            "total_users": len(users),
            "total_messages": total_messages,
            "total_coverage_needs": total_needs,
            "storage_dir": str(self.storage_dir)
        }
