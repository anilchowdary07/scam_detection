"""
Inference script for running the Scam Detection Environment with LLM agents
"""
import os
import sys
from typing import Dict, Any
from openai import OpenAI

from environment import ScamDetectionEnv
from tasks import get_all_tasks


class LLMAgent:
    """LLM-based agent for scam detection"""

    def __init__(self, api_base_url: str, model_name: str, api_key: str):
        """
        Initialize LLM agent

        Args:
            api_base_url: Base URL for OpenAI-compatible API
            model_name: Name of the model to use
            api_key: API key (can be HF_TOKEN or OpenAI key)
        """
        self.client = OpenAI(
            base_url=api_base_url,
            api_key=api_key
        )
        self.model_name = model_name

    def get_action(self, observation: str, step_type: str) -> str:
        """
        Get action from LLM based on observation

        Args:
            observation: Current observation text
            step_type: Type of step (classify/decide/reason)

        Returns:
            Action string
        """
        # Build prompt based on step type
        if step_type == "classify":
            system_prompt = """You are a content moderation AI. Your job is to classify content.
You must respond with EXACTLY one of these formats:
classify('scam')
classify('impersonation')
classify('safe')

Do not include any explanation. Only output the classify command."""

        elif step_type == "decide":
            system_prompt = """You are a content moderation AI. Your job is to decide what action to take.
You must respond with EXACTLY one of these formats:
decide('allow')
decide('remove')
decide('flag')
decide('escalate')

Do not include any explanation. Only output the decide command."""

        elif step_type == "reason":
            system_prompt = """You are a content moderation AI. Your job is to explain your decision.
You must respond with EXACTLY this format:
reason('Your explanation here')

Provide a clear, concise reason. Do not include any other text."""

        else:
            system_prompt = "You are a content moderation AI."

        # Build messages
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": observation}
        ]

        try:
            # Call LLM
            response = self.client.chat.completions.create(
                model=self.model_name,
                messages=messages,
                temperature=0.0,
                max_tokens=200
            )

            action = response.choices[0].message.content.strip()
            return action

        except Exception as e:
            print(f"Error calling LLM: {e}")
            return "noop()"


def run_task(env: ScamDetectionEnv, agent: LLMAgent, max_steps: int = 10) -> Dict[str, Any]:
    """
    Run a single task with the agent

    Args:
        env: Environment instance
        agent: LLM agent
        max_steps: Maximum steps to prevent infinite loops

    Returns:
        Episode results
    """
    # Reset environment
    obs = env.reset()

    total_reward = 0.0
    episode_info = []
    step_count = 0

    done = False

    while not done and step_count < max_steps:
        # Get current step type
        step_type = obs.step_type

        # Build observation text
        obs_text = f"{obs.message}\n\nContent:\n{obs.content}"

        if obs.previous_classification:
            obs_text += f"\n\nPrevious classification: {obs.previous_classification}"
        if obs.previous_decision:
            obs_text += f"\nPrevious decision: {obs.previous_decision}"

        # Get action from agent
        action = agent.get_action(obs_text, step_type)

        print(f"\nStep {step_count + 1} ({step_type}):")
        print(f"Action: {action}")

        # Execute action
        obs, reward, done, info = env.step(action)

        print(f"Reward: {reward:.2f}")

        total_reward += reward
        episode_info.append({
            "step": step_count,
            "step_type": step_type,
            "action": action,
            "reward": float(reward),
            "info": info
        })

        step_count += 1

    # Get final state
    final_state = env.state()

    return {
        "total_reward": float(total_reward),
        "steps": episode_info,
        "final_state": final_state,
        "step_count": step_count
    }


def main():
    """Main inference function"""

    # Read environment variables
    api_base_url = os.getenv("API_BASE_URL", "https://api.openai.com/v1")
    model_name = os.getenv("MODEL_NAME", "gpt-3.5-turbo")
    hf_token = os.getenv("HF_TOKEN", "")
    api_key = os.getenv("OPENAI_API_KEY", hf_token)

    if not api_key:
        print("Error: No API key found. Set OPENAI_API_KEY or HF_TOKEN environment variable.")
        sys.exit(1)

    print("=== Scam Detection Environment - Inference ===")
    print(f"API Base URL: {api_base_url}")
    print(f"Model: {model_name}")
    print("=" * 50)

    # Initialize agent
    agent = LLMAgent(api_base_url, model_name, api_key)

    # Get all tasks
    tasks = get_all_tasks()

    # Run each task
    all_results = []

    for task in tasks:
        print(f"\n{'=' * 50}")
        print(f"Running Task: {task['name']} ({task['difficulty']})")
        print(f"{'=' * 50}")
        print(f"\nContent:\n{task['content']}\n")

        # Create environment
        env = ScamDetectionEnv(task)

        # Run task
        results = run_task(env, agent)

        # Print results
        print(f"\n{'=' * 50}")
        print(f"Results for {task['name']}")
        print(f"{'=' * 50}")
        print(f"Total Reward: {results['total_reward']:.2f}")
        print(f"Steps Taken: {results['step_count']}")

        # Print final grading if available
        if results['steps'] and 'final_grade' in results['steps'][-1]['info']:
            final_grade = results['steps'][-1]['info']['final_grade']
            print(f"\n--- Final Grade ---")
            print(f"Total Score: {final_grade['total']:.2f}")
            print(f"  Classification: {final_grade['classification']:.2f} (weight: {final_grade['classification_weight']})")
            print(f"  Decision: {final_grade['decision']:.2f} (weight: {final_grade['decision_weight']})")
            print(f"  Reasoning: {final_grade['reasoning']:.2f} (weight: {final_grade['reasoning_weight']})")

            # Print what the agent did
            print(f"\n--- Agent Actions ---")
            print(f"Classification: {results['final_state']['classification']}")
            print(f"Decision: {results['final_state']['decision']}")
            print(f"Reasoning: {results['final_state']['reasoning']}")

            # Print expected
            print(f"\n--- Expected ---")
            print(f"Classification: {task['expected_classification']}")
            print(f"Decision: {task['expected_decision']}")
            print(f"Reasoning keywords: {', '.join(task['expected_reasoning_keywords'])}")

        all_results.append({
            "task_name": task['name'],
            "task_difficulty": task['difficulty'],
            "results": results
        })

    # Print summary
    print(f"\n\n{'=' * 50}")
    print("SUMMARY")
    print(f"{'=' * 50}")

    for result in all_results:
        task_name = result['task_name']
        difficulty = result['task_difficulty']
        if result['results']['steps']:
            final_info = result['results']['steps'][-1]['info']
            if 'final_grade' in final_info:
                score = final_info['final_grade']['total']
                print(f"{task_name} ({difficulty}): {score:.2f}")

    print(f"\n{'=' * 50}")


if __name__ == "__main__":
    main()
