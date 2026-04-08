"""
Inference script for running the Scam Detection Environment with LLM agents
OpenEnv compliant with START/STEP/END structured output format
"""
import os
import sys
import json
from typing import Dict, Any

from environment import ScamDetectionEnv
from tasks import get_all_tasks


class LLMAgent:
    """Simple LLM-based agent for scam detection"""

    def __init__(self, api_base_url: str, model_name: str, api_key: str):
        """
        Initialize LLM agent

        Args:
            api_base_url: Base URL for OpenAI-compatible API
            model_name: Name of the model to use
            api_key: API key
        """
        self.api_base_url = api_base_url
        self.model_name = model_name
        self.api_key = api_key

        # Try to import OpenAI client
        try:
            from openai import OpenAI
            self.client = OpenAI(
                base_url=api_base_url,
                api_key=api_key
            )
            self.has_openai = True
        except Exception as e:
            print(f"Warning: Could not initialize OpenAI client: {e}", file=sys.stderr)
            self.has_openai = False

    def get_action(self, observation: str, step_type: str) -> str:
        """
        Get action from LLM based on observation

        Args:
            observation: Current observation text
            step_type: Type of step (classify/decide/reason)

        Returns:
            Action string
        """
        if not self.has_openai or not self.api_key:
            # Fallback: return deterministic actions for testing
            if step_type == "classify":
                return "classify('scam')"
            elif step_type == "decide":
                return "decide('remove')"
            elif step_type == "reason":
                return "reason('This content exhibits characteristics of a scam')"
            else:
                return "noop()"

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
            print(f"Error calling LLM: {e}", file=sys.stderr)
            # Fallback actions
            if step_type == "classify":
                return "classify('scam')"
            elif step_type == "decide":
                return "decide('remove')"
            elif step_type == "reason":
                return "reason('Unable to connect to LLM')"
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
    # Reset environment - returns Observation object
    obs = env.reset()

    total_reward = 0.0
    episode_info = []
    step_count = 0
    done = False

    while not done and step_count < max_steps:
        # Get current step type
        step_type = obs.step_type

        # Build observation text from Observation object
        if hasattr(obs, '__dict__'):
            obs_text = str(obs.message if hasattr(obs, 'message') else "")
            obs_text += f"\n\nContent:\n{obs.content if hasattr(obs, 'content') else ''}"
        else:
            obs_text = str(obs)

        # Get action from agent
        action = agent.get_action(obs_text, step_type)

        # Execute action
        try:
            result = env.step(action)
            if len(result) == 4:
                obs, reward, done, info = result
            else:
                obs, reward, done, info = result[0], result[1], result[2], result[3] if len(result) > 3 else {}
        except Exception as e:
            print(f"Error executing step: {e}", file=sys.stderr)
            reward = 0.0
            done = True
            info = {"error": str(e)}

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
    try:
        final_state = env.state()
    except:
        final_state = {
            "classification": env.classification,
            "decision": env.decision,
            "reasoning": env.reasoning
        }

    return {
        "total_reward": float(total_reward),
        "steps": episode_info,
        "final_state": final_state,
        "step_count": step_count
    }


def main():
    """Main inference function with OpenEnv structured output"""

    # Read environment variables
    api_base_url = os.getenv("API_BASE_URL", "https://api.openai.com/v1")
    model_name = os.getenv("MODEL_NAME", "gpt-3.5-turbo")
    hf_token = os.getenv("HF_TOKEN", "")
    api_key = os.getenv("OPENAI_API_KEY", hf_token)

    # Print START marker (OpenEnv format)
    print("START")
    print(json.dumps({
        "status": "starting",
        "api_base_url": api_base_url,
        "model_name": model_name
    }))

    if not api_key:
        print("Warning: No API key found. Using fallback deterministic actions.")
        print(json.dumps({"warning": "No API key"}))

    # Initialize agent
    agent = LLMAgent(api_base_url, model_name, api_key or "none")

    # Get all tasks
    tasks = get_all_tasks()

    # Run each task
    all_results = []

    for task_idx, task in enumerate(tasks):
        print("STEP")
        print(json.dumps({
            "task_index": task_idx,
            "task_name": task['name'],
            "task_difficulty": task['difficulty'],
            "status": "running"
        }))

        # Create environment
        try:
            env = ScamDetectionEnv(task)

            # Run task
            results = run_task(env, agent)

            # Print task results
            print(json.dumps({
                "task_index": task_idx,
                "task_name": task['name'],
                "total_reward": results['total_reward'],
                "steps_taken": results['step_count'],
                "status": "completed"
            }))

            all_results.append({
                "task_name": task['name'],
                "task_difficulty": task['difficulty'],
                "results": results
            })

        except Exception as e:
            print(json.dumps({
                "task_index": task_idx,
                "task_name": task['name'],
                "error": str(e),
                "status": "failed"
            }))

    # Print END marker (OpenEnv format)
    print("END")
    print(json.dumps({
        "status": "completed",
        "tasks_completed": len(all_results),
        "summary": [
            {
                "task_name": r['task_name'],
                "difficulty": r['task_difficulty'],
                "score": r['results']['total_reward']
            }
            for r in all_results
        ]
    }))


if __name__ == "__main__":
    main()
