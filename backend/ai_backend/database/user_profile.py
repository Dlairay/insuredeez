"""
User Profile Database
Handles CRUD operations for user coverage needs profiles
"""

from datetime import datetime
from typing import Dict, List, Optional
from tinydb import Query
from .db_manager import DatabaseManager


class UserProfileDB:
    """
    Database interface for user coverage needs profiles.
    Stores user itineraries, extracted coverage needs, and preferences.
    """

    def __init__(self):
        """Initialize user profile database"""
        self.db_manager = DatabaseManager()
        self.table = self.db_manager.get_table('user_profiles')
        self.User = Query()

    def create_profile(
        self,
        user_id: str,
        itinerary: str,
        coverage_needs: List[Dict],
        trip_summary: Dict,
        metadata: Optional[Dict] = None
    ) -> int:
        """
        Create a new user coverage needs profile

        Args:
            user_id: Unique user identifier
            itinerary: Original itinerary text
            coverage_needs: List of extracted coverage needs
            trip_summary: Trip summary information
            metadata: Additional metadata

        Returns:
            Document ID of created profile
        """
        profile = {
            "user_id": user_id,
            "itinerary": itinerary,
            "coverage_needs": coverage_needs,
            "trip_summary": trip_summary,
            "metadata": metadata or {},
            "created_at": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat(),
            "status": "active"
        }

        doc_id = self.table.insert(profile)
        print(f"Created profile for user {user_id} with doc_id {doc_id}")
        return doc_id

    def get_profile_by_user_id(self, user_id: str) -> Optional[Dict]:
        """
        Get the most recent profile for a user

        Args:
            user_id: User identifier

        Returns:
            User profile dict or None
        """
        results = self.table.search(self.User.user_id == user_id)
        if not results:
            return None

        # Return most recent profile
        results.sort(key=lambda x: x.get('created_at', ''), reverse=True)
        return results[0]

    def get_profile_by_doc_id(self, doc_id: int) -> Optional[Dict]:
        """
        Get profile by document ID

        Args:
            doc_id: Document ID

        Returns:
            User profile dict or None
        """
        return self.table.get(doc_id=doc_id)

    def get_all_profiles_for_user(self, user_id: str) -> List[Dict]:
        """
        Get all profiles for a user (including history)

        Args:
            user_id: User identifier

        Returns:
            List of user profiles, sorted by creation date (newest first)
        """
        results = self.table.search(self.User.user_id == user_id)
        results.sort(key=lambda x: x.get('created_at', ''), reverse=True)
        return results

    def update_profile(
        self,
        doc_id: int,
        coverage_needs: Optional[List[Dict]] = None,
        trip_summary: Optional[Dict] = None,
        metadata: Optional[Dict] = None,
        status: Optional[str] = None
    ) -> bool:
        """
        Update an existing profile

        Args:
            doc_id: Document ID to update
            coverage_needs: New coverage needs
            trip_summary: New trip summary
            metadata: New metadata
            status: New status

        Returns:
            True if updated, False otherwise
        """
        update_data = {
            "updated_at": datetime.utcnow().isoformat()
        }

        if coverage_needs is not None:
            update_data["coverage_needs"] = coverage_needs
        if trip_summary is not None:
            update_data["trip_summary"] = trip_summary
        if metadata is not None:
            update_data["metadata"] = metadata
        if status is not None:
            update_data["status"] = status

        result = self.table.update(update_data, doc_ids=[doc_id])
        return len(result) > 0

    def add_coverage_need(self, doc_id: int, coverage_need: Dict) -> bool:
        """
        Add a new coverage need to an existing profile

        Args:
            doc_id: Document ID
            coverage_need: Coverage need to add

        Returns:
            True if added, False otherwise
        """
        profile = self.get_profile_by_doc_id(doc_id)
        if not profile:
            return False

        coverage_needs = profile.get('coverage_needs', [])
        coverage_needs.append(coverage_need)

        return self.update_profile(doc_id, coverage_needs=coverage_needs)

    def remove_coverage_need(self, doc_id: int, need_index: int) -> bool:
        """
        Remove a coverage need by index

        Args:
            doc_id: Document ID
            need_index: Index of need to remove

        Returns:
            True if removed, False otherwise
        """
        profile = self.get_profile_by_doc_id(doc_id)
        if not profile:
            return False

        coverage_needs = profile.get('coverage_needs', [])
        if 0 <= need_index < len(coverage_needs):
            coverage_needs.pop(need_index)
            return self.update_profile(doc_id, coverage_needs=coverage_needs)

        return False

    def search_by_tags(self, tags: List[str]) -> List[Dict]:
        """
        Search profiles containing specific taxonomy tags

        Args:
            tags: List of taxonomy tags to search for

        Returns:
            List of matching profiles
        """
        def has_tags(profile):
            profile_tags = set()
            for need in profile.get('coverage_needs', []):
                profile_tags.update(need.get('taxonomy_tags', []))
            return any(tag in profile_tags for tag in tags)

        all_profiles = self.table.all()
        return [p for p in all_profiles if has_tags(p)]

    def search_by_priority(self, priority: str) -> List[Dict]:
        """
        Search profiles with specific priority needs

        Args:
            priority: Priority level (HIGH, MEDIUM, LOW)

        Returns:
            List of matching profiles
        """
        def has_priority(profile):
            for need in profile.get('coverage_needs', []):
                if need.get('priority') == priority:
                    return True
            return False

        all_profiles = self.table.all()
        return [p for p in all_profiles if has_priority(p)]

    def delete_profile(self, doc_id: int) -> bool:
        """
        Delete a profile

        Args:
            doc_id: Document ID to delete

        Returns:
            True if deleted, False otherwise
        """
        result = self.table.remove(doc_ids=[doc_id])
        return len(result) > 0

    def get_stats(self) -> Dict:
        """
        Get statistics about stored profiles

        Returns:
            Dictionary with stats
        """
        all_profiles = self.table.all()

        total_needs = 0
        priority_counts = {"HIGH": 0, "MEDIUM": 0, "LOW": 0}
        all_tags = set()

        for profile in all_profiles:
            needs = profile.get('coverage_needs', [])
            total_needs += len(needs)

            for need in needs:
                priority = need.get('priority', 'UNKNOWN')
                if priority in priority_counts:
                    priority_counts[priority] += 1

                all_tags.update(need.get('taxonomy_tags', []))

        return {
            "total_profiles": len(all_profiles),
            "total_coverage_needs": total_needs,
            "unique_taxonomy_tags": len(all_tags),
            "priority_distribution": priority_counts,
            "avg_needs_per_profile": total_needs / len(all_profiles) if all_profiles else 0
        }
