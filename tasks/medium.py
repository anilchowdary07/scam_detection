"""
Medium task: Impersonation report
"""

TASK = {
    "name": "medium_impersonation",
    "difficulty": "medium",
    "content": "Hi everyone! I'm Elon Musk and I'm giving away Bitcoin! Send 1 BTC to this address: 1A1zP1eP5QGefi2DMPTfTL5SLmv7DivfNa and I'll send you back 2 BTC! This is a limited time offer! Follow my new Twitter account @elonmusk_official for more updates! Hurry before the giveaway ends!",
    "expected_classification": "impersonation",
    "expected_decision": "remove",
    "expected_reasoning_keywords": ["impersonation", "fake", "celebrity", "giveaway", "scam", "cryptocurrency"],
    "strong_keywords": ["impersonation", "fake", "scam"],
    "description": "Celebrity impersonation cryptocurrency scam"
}
