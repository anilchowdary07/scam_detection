"""
Hard task: Subtle and ambiguous phishing/scam
"""

TASK = {
    "name": "hard_subtle_phishing",
    "difficulty": "hard",
    "content": "Hello, We've detected a login from a new device on your account. Location: San Francisco, CA. Date: March 28, 2026 at 2:14 PM. If this was you, no action is needed. If you don't recognize this activity, please secure your account by reviewing your security settings at: https://account-security-check.online/verify?ref=sf2826 This link expires in 24 hours. Our team is here to help keep your account safe. Thank you for being a valued member.",
    "expected_classification": "scam",
    "expected_decision": "flag",
    "expected_reasoning_keywords": ["phishing", "suspicious", "link", "verify", "domain", "urgency", "legitimate-seeming"],
    "strong_keywords": ["phishing", "suspicious", "domain"],
    "description": "Highly subtle phishing with legitimate-looking security alert"
}
