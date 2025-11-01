"""
Profile Manager - File-based user profile storage system

Stores user profiles as Python files in the artifacts/ directory.
Each profile is stored as: artifacts/user_{user_id}_profile.py

The file contains a PROFILE constant with the user's data as a dictionary.
"""

import os
import importlib.util
import sys
from pathlib import Path
from typing import Dict, Optional
from datetime import datetime
import pprint

# Import the schema template for default profile structure
from schema_template import taxonomy_dict

# Base directory for artifacts
ARTIFACTS_DIR = Path("/Users/ray/Desktop/hackdeez/backend/ai_backend/agents/artifacts")


def get_profile_path(user_id: str) -> Path:
    """
    Get the file path for a user's profile.

    Args:
        user_id: The user's unique identifier

    Returns:
        Path object pointing to the user's profile file
    """
    # Sanitize user_id to be filesystem-safe
    safe_user_id = user_id.replace("/", "_").replace("\\", "_")
    return ARTIFACTS_DIR / f"user_{safe_user_id}_profile.py"


def load_profile(user_id: str) -> Dict:
    """
    Load a user's profile from their Python file.

    If the profile doesn't exist, returns a new profile based on the schema template.

    Args:
        user_id: The user's unique identifier

    Returns:
        Dictionary containing the user's profile data
    """
    profile_path = get_profile_path(user_id)

    # If profile doesn't exist, return a new one from template
    if not profile_path.exists():
        print(f"Profile not found for user {user_id}, creating new profile from template")
        new_profile = taxonomy_dict.copy()
        # Set default names for mainContact
        new_profile["mainContact"]["firstName"] = "John"
        new_profile["mainContact"]["lastName"] = "Doe"
        return new_profile

    try:
        # Load the Python module dynamically
        spec = importlib.util.spec_from_file_location(f"user_{user_id}_profile", profile_path)
        if spec is None or spec.loader is None:
            raise ImportError(f"Could not load profile from {profile_path}")

        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)

        # Get the PROFILE constant from the module
        if not hasattr(module, 'PROFILE'):
            raise AttributeError(f"Profile file {profile_path} does not contain PROFILE constant")

        profile = module.PROFILE
        print(f"Loaded profile for user {user_id} from {profile_path}")
        return profile

    except Exception as e:
        print(f"Error loading profile for user {user_id}: {e}")
        print(f"Returning new profile from template")
        new_profile = taxonomy_dict.copy()
        new_profile["mainContact"]["firstName"] = "John"
        new_profile["mainContact"]["lastName"] = "Doe"
        return new_profile


def save_profile(user_id: str, profile_data: Dict) -> bool:
    """
    Save a user's profile to their Python file.

    Args:
        user_id: The user's unique identifier
        profile_data: Dictionary containing the profile data to save

    Returns:
        True if save was successful, False otherwise
    """
    profile_path = get_profile_path(user_id)

    try:
        # Ensure artifacts directory exists
        ARTIFACTS_DIR.mkdir(parents=True, exist_ok=True)

        # Add metadata
        profile_data['user_id'] = user_id
        profile_data['updated_at'] = datetime.now().isoformat()

        # Convert the profile dict to a nicely formatted Python string using pprint
        profile_str = pprint.pformat(profile_data, indent=2, width=120)

        # Write as a Python file with PROFILE constant
        python_content = f'''"""
User Profile for {user_id}
Generated: {datetime.now().isoformat()}
"""

PROFILE = {profile_str}
'''

        profile_path.write_text(python_content, encoding='utf-8')
        print(f"Saved profile for user {user_id} to {profile_path}")
        return True

    except Exception as e:
        print(f"Error saving profile for user {user_id}: {e}")
        return False


def delete_profile(user_id: str) -> bool:
    """
    Delete a user's profile file.

    Args:
        user_id: The user's unique identifier

    Returns:
        True if deletion was successful or file didn't exist, False if error occurred
    """
    profile_path = get_profile_path(user_id)

    try:
        if profile_path.exists():
            profile_path.unlink()
            print(f"Deleted profile for user {user_id}")
            return True
        else:
            print(f"Profile for user {user_id} does not exist, nothing to delete")
            return True

    except Exception as e:
        print(f"Error deleting profile for user {user_id}: {e}")
        return False


def profile_exists(user_id: str) -> bool:
    """
    Check if a profile file exists for a user.

    Args:
        user_id: The user's unique identifier

    Returns:
        True if profile file exists, False otherwise
    """
    profile_path = get_profile_path(user_id)
    return profile_path.exists()
