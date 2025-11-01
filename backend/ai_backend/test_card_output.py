"""
Test new card-based output format
"""
import os
import sys
from dotenv import load_dotenv

load_dotenv()
os.environ['CURRENT_USER_ID'] = 'test_card_user'

sys.path.append('/Users/ray/Desktop/hackdeez/backend/ai_backend')
from agents.Conversation_agent.helper_agents.policy_recommendation_agent.tools import (
    analyze_itinerary_needs,
    select_best_plan
)
from profile_manager import delete_profile
import json

# Clean start
delete_profile('test_card_user')

# Quick test
itinerary = "Going to Bali for surfing and diving"

print("Testing new card output format...\n")

# Step 1: Analyze needs
result1 = analyze_itinerary_needs(itinerary)
print(f"✅ Needs identified: {len(result1.get('identified_needs', []))}\n")

# Step 2: Get plan cards
result2 = select_best_plan()

print("=" * 80)
print("CARD OUTPUT FORMAT")
print("=" * 80)
print(json.dumps(result2, indent=2))

print("\n" + "=" * 80)
print("FRONTEND CAN DISPLAY 3 CARDS:")
print("=" * 80)

for product_name, product_data in result2.get('products', {}).items():
    print(f"\n📋 {product_name}")
    print(f"   Match: {product_data['match_percentage']}%")
    print(f"   Needs: {product_data['needs_matched']}/{product_data['total_needs']}")
    print(f"   Recommended: {'✅ YES' if product_data['is_recommended'] else '❌ No'}")
    print(f"   Matched needs: {', '.join(product_data['matched_needs'][:3])}...")
