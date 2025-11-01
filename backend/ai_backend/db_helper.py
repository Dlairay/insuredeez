"""
Database Helper Functions
Connects to PostgreSQL to fetch real historical claims data
"""

import os
import psycopg2
from typing import Dict, Optional

def get_claim_stats(destination: str) -> Optional[Dict]:
    """
    Fetch real historical claim statistics from PostgreSQL database

    Queries the claims database to find:
    1. Most common claim type for this destination
    2. Most common cause of loss for that claim type
    3. Average gross incurred amount for those claims

    Args:
        destination: Country name (e.g., "Indonesia", "Thailand")

    Returns:
        Dictionary with claim statistics or None if query fails
        {
            'destination': str,
            'claim_type': str,
            'cause_of_loss': str,
            'gross_incurred': float
        }
    """
    try:
        # Connect to PostgreSQL
        conn = psycopg2.connect(
            dbname=os.getenv('POSTGRES_DB', 'hackathon_db'),
            user=os.getenv('POSTGRES_USER', 'hackathon_user'),
            password=os.getenv('POSTGRES_PASSWORD', 'Hackathon2025!'),
            host=os.getenv('POSTGRES_HOST', 'hackathon-db.ceqjfmi6jhdd.ap-southeast-1.rds.amazonaws.com'),
            port=os.getenv('POSTGRES_PORT', '5432')
        )
        cur = conn.cursor()

        # Step 1: Find most common claim type for this destination
        cur.execute("""
            SELECT claim_type, COUNT(*) as count
            FROM hackathon.claims
            WHERE LOWER(destination) = LOWER(%s)
            GROUP BY claim_type
            ORDER BY count DESC
            LIMIT 1
        """, (destination,))

        row = cur.fetchone()
        if not row:
            print(f"[WARNING] No claims data found for destination: {destination}")
            cur.close()
            conn.close()
            return None

        claim_type = row[0]
        print(f"[DEBUG] Most common claim type for {destination}: {claim_type}")

        # Step 2: Find most common cause of loss for this claim type
        cur.execute("""
            SELECT cause_of_loss, COUNT(*) as count
            FROM hackathon.claims
            WHERE LOWER(destination) = LOWER(%s) AND claim_type = %s
            GROUP BY cause_of_loss
            ORDER BY count DESC
            LIMIT 1
        """, (destination, claim_type))

        row = cur.fetchone()
        cause_of_loss = row[0] if row else "Unknown"
        print(f"[DEBUG] Most common cause: {cause_of_loss}")

        # Step 3: Calculate average claim amount
        cur.execute("""
            SELECT AVG(gross_incurred)
            FROM hackathon.claims
            WHERE LOWER(destination) = LOWER(%s) AND claim_type = %s AND cause_of_loss = %s
        """, (destination, claim_type, cause_of_loss))

        avg_amount = cur.fetchone()[0] or 0.0

        cur.close()
        conn.close()

        result = {
            'destination': destination,
            'claim_type': claim_type,
            'cause_of_loss': cause_of_loss,
            'gross_incurred': float(avg_amount)
        }

        print(f"[DEBUG] DB Stats: {result}")
        return result

    except Exception as e:
        print(f"[ERROR] Database query failed: {e}")
        return None
