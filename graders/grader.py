"""
Deterministic grader for scam detection tasks (IMPROVED)
"""
from typing import Dict, Any, Tuple


class ScamDetectionGrader:
    """
    Deterministic grader with quality-based scoring

    Features:
    - Exact match grading for classification and decision
    - Quality-tiered reasoning evaluation (strong/medium/weak)
    - Partial credit for keyword matching
    """

    def __init__(self, task: Dict[str, Any]):
        self.task = task
        self.expected_classification = task["expected_classification"]
        self.expected_decision = task["expected_decision"]
        self.expected_keywords = task["expected_reasoning_keywords"]

        # Define strong keywords (more critical indicators)
        self.strong_keywords = task.get("strong_keywords", self.expected_keywords[:3])

    def grade_classification(self, classification: str) -> float:
        """
        Grade classification step
        Returns 1.0 if correct, 0.0 if incorrect
        """
        if classification.lower().strip() == self.expected_classification.lower().strip():
            return 1.0
        return 0.0

    def grade_decision(self, decision: str) -> float:
        """
        Grade decision step
        Returns 1.0 if correct, 0.0 if incorrect
        """
        if decision.lower().strip() == self.expected_decision.lower().strip():
            return 1.0
        return 0.0

    def grade_reasoning(self, reasoning: str) -> Tuple[float, str]:
        """
        Grade reasoning step with quality assessment

        Returns:
            Tuple of (score: float, quality: str)
            - score: 0.0 to 1.0
            - quality: 'strong', 'medium', or 'weak'
        """
        reasoning_lower = reasoning.lower()
        matched_keywords = 0
        strong_matches = 0

        # Count all keyword matches
        for keyword in self.expected_keywords:
            if keyword.lower() in reasoning_lower:
                matched_keywords += 1

        # Count strong keyword matches
        for keyword in self.strong_keywords:
            if keyword.lower() in reasoning_lower:
                strong_matches += 1

        if len(self.expected_keywords) == 0:
            return 1.0, "strong"

        # Calculate match percentage
        match_percentage = float(matched_keywords) / float(len(self.expected_keywords))
        strong_percentage = float(strong_matches) / float(len(self.strong_keywords)) if self.strong_keywords else 0.0

        # Determine quality tier
        if match_percentage >= 0.66 and strong_percentage >= 0.66:
            quality = "strong"  # Strong match: 66%+ keywords including critical ones
            score = match_percentage
        elif match_percentage >= 0.33:
            quality = "medium"  # Medium match: 33-66% keywords
            score = match_percentage
        else:
            quality = "weak"  # Weak match: <33% keywords
            score = match_percentage

        # Ensure score is in 0.0-1.0 range
        score = max(0.0, min(1.0, score))

        return score, quality

    def grade_episode(
        self,
        classification: str,
        decision: str,
        reasoning: str
    ) -> Dict[str, float]:
        """
        Grade entire episode and return breakdown

        Scoring:
        - Classification: 0.3 weight (CRITICAL)
        - Decision: 0.4 weight
        - Reasoning: 0.3 weight
        """
        classification_score = self.grade_classification(classification)
        decision_score = self.grade_decision(decision)
        reasoning_score, quality = self.grade_reasoning(reasoning)

        # Weighted total
        total_score = (
            classification_score * 0.3 +
            decision_score * 0.4 +
            reasoning_score * 0.3
        )

        # Ensure all values are floats in 0.0-1.0 range
        return {
            "total": float(max(0.0, min(1.0, total_score))),
            "classification": float(classification_score),
            "decision": float(decision_score),
            "reasoning": float(reasoning_score),
            "reasoning_quality": quality,
            "classification_weight": 0.3,
            "decision_weight": 0.4,
            "reasoning_weight": 0.3
        }
