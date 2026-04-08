"""
Inference script for running the Scam Detection Environment with LLM agents
OpenEnv compliant with START/STEP/END structured output format
"""
import os
import sys
from typing import List

from environment import ScamDetectionEnv
from tasks import get_all_tasks


class LLMAgent:
    """Simple LLM-based agent for scam detection"""

    def __init__(self, api_base_url: str, model_name: str, api_key: str):
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

    def get_action(self, observation_str: str, step_type: str) -> str:
        """Get action from LLM based on observation"""
        if not self.has_openai or not self.api_key:
            # Fallback: return deterministic actions
            if step_type == "classify":
                if "Elon" in observation_str or "Bitcoin" in observation_str:
                    return "classify('impersonation')"
                elif "URGENT" in observation_str or "password" in observation_str:
                    return "classify('scam')"
                return "classify('safe')"
            elif step_type == "decide":
                return "decide('remove')"
            elif step_type == "reason":
                return "reason('This content exhibits characteristics of a scam or impersonation')"
            return "noop()"

        # Build prompt for LLM
        prompt = f"""You are a content moderation AI. 

Current step: {step_type}

Observation: {observation_str}

"""
        if step_type == "classify":
            prompt += "Classify this as 'scam', 'impersonation', or 'safe'. Respond with ONLY: classify('scam') or classify('impersonation') or classify('safe')"
        elif step_type == "decide":
            prompt += "Decide action: 'allow', 'remove', 'flag', or 'escalate'. Respond with ONLY: decide('remove') or decide('allow') etc."
        elif step_type == "reason":
            prompt += "Provide reasoning in 1 sentence. Respond with ONLY: reason('your explanation')"

        try:
            response = self.client.chat.completions.create(
                model=self.model_name,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.0,
                max_tokens=100
            )
            action = response.choices[0].message.content.strip()
            return action
        except Exception as e:
            print(f"Error calling LLM: {e}", file=sys.stderr)
            # Fallback
            if step_type == "classify":
                return "classify('scam')"
            elif step_type == "decide":
                return "decide('remove')"
            return "reason('Error calling LLM')"


def run_task(task, agent: LLMAgent, task_name: str, env_name: str, model_name: str, max_steps: int = 10):
    """
    Run a single task with structured output
    
    Emits:
    [START] task=<task_name> env=<benchmark> model=<model_name>
    [STEP]  step=<n> action=<action_str> reward=<0.00> done=<true|false> error=<msg|null>
    [END]   success=<true|false> steps=<n> score=<score> rewards=<r1,r2,...,rn>
    """
    # Print [START] line
    print(f"[START] task={task_name} env={env_name} model={model_name}")
    
    # Create environment
    env = ScamDetectionEnv(task)
    
    # Reset environment
    obs = env.reset()
    
    rewards: List[float] = []
    step_count = 0
    done = False
    total_reward = 0.0
    
    while not done and step_count < max_steps:
        step_count += 1
        
        # Get observation text
        step_type = obs.step_type if hasattr(obs, 'step_type') else 'unknown'
        obs_text = f"{obs.message}\n{obs.content}" if hasattr(obs, 'message') else str(obs)
        
        # Get action from agent
        try:
            action = agent.get_action(obs_text, step_type)
        except Exception as e:
            action = "noop()"
            error_msg = str(e)
            print(f"[STEP] step={step_count} action={repr(action)} reward=0.00 done=true error={repr(error_msg)}")
            rewards.append(0.0)
            break
        
        # Execute step
        try:
            obs, reward, done, info = env.step(action)
            error_msg = info.get('error', None) if isinstance(info, dict) else None
        except Exception as e:
            reward = 0.0
            done = True
            error_msg = str(e)
            obs = None
        
        # Store reward
        rewards.append(float(reward))
        total_reward += float(reward)
        
        # Print [STEP] line
        done_str = "true" if done else "false"
        error_str = repr(error_msg) if error_msg else "null"
        action_clean = action.replace('\n', ' ').replace('\r', '')
        print(f"[STEP] step={step_count} action={repr(action_clean)} reward={reward:.2f} done={done_str} error={error_str}")
    
    # Calculate final score and enforce strict validator bounds: (0, 1)
    # Hackathon validator rejects exactly 0.00 and 1.00.
    raw_score = min(1.0, max(0.0, total_reward))
    epsilon = 0.01
    score = min(1.0 - epsilon, max(epsilon, raw_score))
    
    # Print [END] line
    success_str = "true" if done and total_reward > 0 else "false"
    rewards_str = ",".join([f"{r:.2f}" for r in rewards])
    print(f"[END] success={success_str} steps={step_count} score={score:.2f} rewards={rewards_str}")
    
    return score


def main():
    """Main inference function"""
    # Read environment variables
    api_base_url = os.getenv("API_BASE_URL", "https://api.openai.com/v1")
    model_name = os.getenv("MODEL_NAME", "gpt-3.5-turbo")
    # Phase-2 validator injects API_KEY/API_BASE_URL through its LiteLLM proxy.
    api_key = os.getenv("API_KEY") or os.getenv("OPENAI_API_KEY") or os.getenv("HF_TOKEN", "")
    
    if not api_key:
        print("Warning: No API key found. Using deterministic fallback actions.", file=sys.stderr)
    
    # Initialize agent
    agent = LLMAgent(api_base_url, model_name, api_key or "none")
    
    # Get all tasks
    tasks = get_all_tasks()
    env_name = "scam-detection"
    
    # Run each task
    all_scores = []
    for task in tasks:
        task_name = task.get('name', task.get('difficulty', 'unknown'))
        score = run_task(task, agent, task_name, env_name, model_name)
        all_scores.append(score)
    
    # Print summary to stderr (not stdout to avoid breaking format)
    print(f"\n=== SUMMARY ===", file=sys.stderr)
    print(f"Tasks completed: {len(all_scores)}", file=sys.stderr)
    print(f"Average score: {sum(all_scores)/len(all_scores) if all_scores else 0:.2f}", file=sys.stderr)


if __name__ == "__main__":
    main()
