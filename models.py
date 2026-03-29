"""
Pydantic models for the Scam Detection Environment
"""
from pydantic import BaseModel, Field
from typing import Optional, Literal
import re


class Observation(BaseModel):
    """Observation returned by the environment"""
    step_type: Literal["classify", "decide", "reason"]
    content: str
    previous_classification: Optional[str] = None
    previous_decision: Optional[str] = None
    message: str = ""


class Action(BaseModel):
    """Action taken by the agent"""
    action_type: Literal["classify", "decide", "reason", "noop"]
    value: str

    @classmethod
    def parse_action(cls, action_str: str) -> "Action":
        """Parse action string into Action model"""
        # Try to match classify('...')
        classify_match = re.search(r"classify\(['\"](.+?)['\"]\)", action_str, re.IGNORECASE | re.DOTALL)
        if classify_match:
            return cls(action_type="classify", value=classify_match.group(1).strip())

        # Try to match decide('...')
        decide_match = re.search(r"decide\(['\"](.+?)['\"]\)", action_str, re.IGNORECASE | re.DOTALL)
        if decide_match:
            return cls(action_type="decide", value=decide_match.group(1).strip())

        # Try to match reason('...')
        reason_match = re.search(r"reason\(['\"](.+?)['\"]\)", action_str, re.IGNORECASE | re.DOTALL)
        if reason_match:
            return cls(action_type="reason", value=reason_match.group(1).strip())

        # Default to noop
        return cls(action_type="noop", value="")


class Reward(BaseModel):
    """Reward structure"""
    total: float = Field(default=0.0, description="Total reward for the step")
    classification_score: float = Field(default=0.0, description="Score for classification")
    decision_score: float = Field(default=0.0, description="Score for decision")
    reasoning_score: float = Field(default=0.0, description="Score for reasoning")
    correct: bool = Field(default=False, description="Whether the action was correct")
