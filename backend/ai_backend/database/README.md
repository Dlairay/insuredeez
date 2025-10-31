# Database Module

TinyDB-based NoSQL database for storing user coverage needs profiles.

## Overview

This module provides a lightweight, file-based database solution for storing and querying user travel insurance coverage needs profiles. It uses TinyDB, which stores data as JSON files in the `ai_backend/database/` directory.

## Structure

```
database/
├── __init__.py              # Module exports
├── db_manager.py            # DatabaseManager - handles TinyDB connections
├── user_profile.py          # UserProfileDB - CRUD operations for profiles
├── data.json                # Database file (created on first use)
├── requirements.txt         # Dependencies (tinydb)
├── test_db.py              # Test script for database operations
├── integration_example.py   # End-to-end example with needs extraction
└── README.md               # This file
```

## Installation

```bash
cd /Users/ray/Desktop/hackdeez/backend/ai_backend/database
pip install -r requirements.txt
```

## Usage

### Basic CRUD Operations

```python
from database.user_profile import UserProfileDB

# Initialize database
db = UserProfileDB()

# Create a profile
doc_id = db.create_profile(
    user_id="user_001",
    itinerary="Trip to Japan...",
    coverage_needs=[
        {
            "need_category": "layer_2_benefits",
            "taxonomy_tags": ["trip_cancellation"],
            "reasoning": "Expensive non-refundable bookings",
            "priority": "HIGH",
            "itinerary_evidence": "Non-refundable flights $10k"
        }
    ],
    trip_summary={
        "destinations": ["Japan"],
        "duration_days": 14
    }
)

# Retrieve profile
profile = db.get_profile_by_user_id("user_001")

# Search by taxonomy tags
medical_profiles = db.search_by_tags(["overseas_medical_expenses"])

# Search by priority
high_priority = db.search_by_priority("HIGH")

# Update profile
db.add_coverage_need(doc_id, {
    "taxonomy_tags": ["personal_belongings"],
    "priority": "MEDIUM"
})

# Get statistics
stats = db.get_stats()
```

### Integration with Needs Extraction Agent

```python
from agents.needs_extraction_agent.agent import NeedsExtractionAgent
from database.user_profile import UserProfileDB

# Extract needs from itinerary
agent = NeedsExtractionAgent()
result = agent.extract_needs_with_keyword_boost(itinerary, verbose=True)

# Save to database
db = UserProfileDB()
doc_id = db.create_profile(
    user_id="user_123",
    itinerary=itinerary,
    coverage_needs=result['coverage_needs'],
    trip_summary=result['trip_summary'],
    metadata=result['_metadata']
)
```

## User Profile Schema

```json
{
  "user_id": "string",
  "itinerary": "string",
  "coverage_needs": [
    {
      "need_category": "layer_1_general_conditions | layer_2_benefits | layer_3_benefit_specific_conditions",
      "taxonomy_tags": ["tag1", "tag2"],
      "reasoning": "string",
      "priority": "HIGH | MEDIUM | LOW",
      "itinerary_evidence": "string",
      "source": "llm_extraction | keyword_detection"
    }
  ],
  "trip_summary": {
    "destinations": ["string"],
    "duration_days": "number",
    "activities": ["string"],
    "risk_factors": ["string"],
    "traveler_profile": {}
  },
  "metadata": {
    "total_tags": "number",
    "valid_tags": "number",
    "model_used": "string",
    "keyword_boost_enabled": "boolean"
  },
  "created_at": "ISO datetime string",
  "updated_at": "ISO datetime string",
  "status": "active | archived"
}
```

## DatabaseManager API

### Methods

- `get_table(table_name)` - Get or create a table
- `list_tables()` - List all tables
- `drop_table(table_name)` - Drop a table
- `get_stats()` - Get database statistics
- `close()` - Close database connection

## UserProfileDB API

### Create
- `create_profile(user_id, itinerary, coverage_needs, trip_summary, metadata)` - Create new profile

### Read
- `get_profile_by_user_id(user_id)` - Get most recent profile for user
- `get_profile_by_doc_id(doc_id)` - Get profile by document ID
- `get_all_profiles_for_user(user_id)` - Get profile history for user

### Update
- `update_profile(doc_id, ...)` - Update profile fields
- `add_coverage_need(doc_id, coverage_need)` - Add a coverage need
- `remove_coverage_need(doc_id, need_index)` - Remove a coverage need

### Search
- `search_by_tags(tags)` - Find profiles with specific taxonomy tags
- `search_by_priority(priority)` - Find profiles with specific priority needs

### Delete
- `delete_profile(doc_id)` - Delete a profile

### Stats
- `get_stats()` - Get database statistics

## Test Scripts

### Test Database Operations
```bash
python test_db.py
```

Tests:
- Creating profiles
- Retrieving profiles
- Updating profiles
- Searching by tags and priority
- Database statistics

### Test Integration
```bash
python integration_example.py
```

Demonstrates:
- End-to-end flow: itinerary → extraction → database
- Querying saved profiles
- Using taxonomy tags for search

## Database File

The database is stored as a JSON file at:
```
/Users/ray/Desktop/hackdeez/backend/ai_backend/database/data.json
```

It's human-readable and can be inspected/edited directly if needed.

## Features

✅ **Singleton Pattern** - Single database instance across application
✅ **Caching Middleware** - Fast read/write performance
✅ **Auto-indexing** - TinyDB handles indexing automatically
✅ **JSON Storage** - Human-readable, easy to debug
✅ **No External Server** - File-based, perfect for development
✅ **Type-safe Queries** - Query() API for safe searches
✅ **Flexible Schema** - NoSQL allows schema evolution

## Shared Resource

This database is designed as a **shared resource** that multiple agents can use:
- `needs_extraction_agent` - Saves extracted coverage needs
- `policy_intelligence_agent` - Can query user needs for matching
- Future agents - Can add/query user profiles

All agents access the same `data.json` file through the DatabaseManager singleton.
