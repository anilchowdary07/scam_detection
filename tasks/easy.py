"""
Easy task: Obvious scam message
"""

TASK = {
    "name": "easy_scam",
    "difficulty": "easy",
    "content": "URGENT! Your bank account has been compromised! Click here immediately: http://fake-bank-login.com Enter your username, password, and social security number to verify your identity. If you don't act within 24 hours, your account will be permanently locked!",
    "expected_classification": "scam",
    "expected_decision": "remove",
    "expected_reasoning_keywords": ["phishing", "credentials", "urgent", "fake", "suspicious", "scam"],
    "strong_keywords": ["phishing", "credentials", "fake"],
    "description": "An obvious phishing scam asking for sensitive information"
}
