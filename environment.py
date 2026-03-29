"""
OpenEnv-compliant Scam Detection Environment (IMPROVED)
"""
from typing import Tuple, Dict, Any
from models import Observation, Action
from graders import ScamDetectionGrader


class ScamDetectionEnv:
    """
    Multi-step scam detection environment with dynamic behavior

    Features:
    - Early termination on critical mistakes
    - Progressive penalties for repeated errors
    - Quality-based reward shaping
    - Strict action sequence enforcement
    """

    def __init__(self, task: Dict[str, Any]):
        """
        Initialize environment with a task

        Args:
            task: Dictionary containing task information
        """
        self.task = task
        self.grader = ScamDetectionGrader(task)

        # Episode state
        self.current_step = 0
        self.max_steps = 3
        self.classification = None
        self.decision = None
        self.reasoning = None

        # Mistake tracking for progressive penalties
        self.mistake_count = 0
        self.consecutive_mistakes = 0

        # Current observation
        self._current_observation = None

    def reset(self) -> Observation:
        """
        Reset the environment to initial state

        Returns:
            Initial observation
        """
        self.current_step = 0
        self.classification = None
        self.decision = None
        self.reasoning = None
        self.mistake_count = 0
        self.consecutive_mistakes = 0

        self._current_observation = Observation(
            step_type="classify",
            content=self.task["content"],
            message="Classify this content as 'scam', 'impersonation', or 'safe'"
        )

        return self._current_observation

    def step(self, action: str) -> Tuple[Observation, float, bool, Dict[str, Any]]:
        """
        Execute one step in the environment with dynamic behavior

        Args:
            action: Action string (e.g., "classify('scam')")

        Returns:
            Tuple of (observation, reward, done, info)
        """
        # Parse action
        parsed_action = Action.parse_action(action)

        # Initialize reward as float
        reward = 0.0
        done = False
        info = {
            "step": self.current_step,
            "action_type": parsed_action.action_type,
            "action_value": parsed_action.value,
            "mistake_count": self.mistake_count
        }

        # Calculate progressive penalty multiplier
        penalty_multiplier = 1.0 + (0.1 * self.consecutive_mistakes)

        # Step 0: Classification (CRITICAL STEP)
        if self.current_step == 0:
            if parsed_action.action_type == "classify":
                self.classification = parsed_action.value
                classification_score = self.grader.grade_classification(self.classification)

                if classification_score == 1.0:
                    # Correct classification
                    reward = 0.3
                    self.consecutive_mistakes = 0
                    info["classification_correct"] = True
                    info["classification_score"] = 1.0

                    # Progress to next step
                    self.current_step += 1
                    self._current_observation = Observation(
                        step_type="decide",
                        content=self.task["content"],
                        previous_classification=self.classification,
                        message="Decide the action: 'allow', 'remove', 'flag', or 'escalate'"
                    )
                else:
                    # WRONG classification - EARLY TERMINATION
                    reward = -0.3 * penalty_multiplier
                    done = True  # End episode immediately
                    self.mistake_count += 1
                    self.consecutive_mistakes += 1
                    info["classification_correct"] = False
                    info["classification_score"] = 0.0
                    info["early_termination"] = "Wrong classification"

                    # Final observation
                    self._current_observation = Observation(
                        step_type="classify",
                        content="Episode ended due to wrong classification",
                        message="Wrong classification - episode terminated"
                    )
            else:
                # Wrong action type at this step
                reward = -0.2 * penalty_multiplier
                self.mistake_count += 1
                self.consecutive_mistakes += 1
                info["error"] = "Expected classify action"
                # Don't progress - keep same observation

        # Step 1: Decision (only if classification was correct)
        elif self.current_step == 1:
            if parsed_action.action_type == "decide":
                self.decision = parsed_action.value
                decision_score = self.grader.grade_decision(self.decision)

                if decision_score == 1.0:
                    # Correct decision
                    reward = 0.4
                    self.consecutive_mistakes = 0
                    info["decision_correct"] = True
                    info["decision_score"] = 1.0

                    # Progress to next step
                    self.current_step += 1
                    self._current_observation = Observation(
                        step_type="reason",
                        content=self.task["content"],
                        previous_classification=self.classification,
                        previous_decision=self.decision,
                        message="Provide reasoning for your decision"
                    )
                else:
                    # Wrong decision - apply penalty but allow continuation
                    reward = -0.2 * penalty_multiplier
                    self.mistake_count += 1
                    self.consecutive_mistakes += 1
                    info["decision_correct"] = False
                    info["decision_score"] = 0.0
                    # Don't progress - keep same observation
            else:
                # Wrong action type
                reward = -0.2 * penalty_multiplier
                self.mistake_count += 1
                self.consecutive_mistakes += 1
                info["error"] = "Expected decide action"
                # Don't progress

        # Step 2: Reasoning (only if previous steps were correct)
        elif self.current_step == 2:
            if parsed_action.action_type == "reason":
                self.reasoning = parsed_action.value
                reasoning_score, quality = self.grader.grade_reasoning(self.reasoning)

                # Quality-based rewards
                if quality == "strong":
                    reward = 0.3  # Strong keyword match
                elif quality == "medium":
                    reward = 0.15  # Partial match
                else:
                    reward = 0.0  # Weak or no match

                self.consecutive_mistakes = 0
                info["reasoning_score"] = float(reasoning_score)
                info["reasoning_quality"] = quality

                # Complete episode
                self.current_step += 1
                done = True
                self._current_observation = Observation(
                    step_type="classify",
                    content="Episode completed",
                    message="Episode completed successfully"
                )
            else:
                # Wrong action type
                reward = -0.2 * penalty_multiplier
                self.mistake_count += 1
                self.consecutive_mistakes += 1
                info["error"] = "Expected reason action"
                # Don't progress

        # Check if max steps reached (fallback)
        if self.current_step >= self.max_steps:
            done = True

        # Add final grading if done
        if done:
            final_grade = self.grader.grade_episode(
                self.classification or "",
                self.decision or "",
                self.reasoning or ""
            )
            info["final_grade"] = final_grade
            info["total_mistakes"] = self.mistake_count

        # Ensure reward is float and bounded
        reward = float(max(-1.0, min(1.0, reward)))

        return self._current_observation, reward, done, info

    def state(self) -> Dict[str, Any]:
        """
        Get current environment state

        Returns:
            Dictionary containing current state
        """
        return {
            "current_step": self.current_step,
            "max_steps": self.max_steps,
            "classification": self.classification,
            "decision": self.decision,
            "reasoning": self.reasoning,
            "mistake_count": self.mistake_count,
            "consecutive_mistakes": self.consecutive_mistakes,
            "task_name": self.task["name"],
            "task_difficulty": self.task["difficulty"]
        }
