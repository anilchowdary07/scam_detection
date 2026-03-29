"""
FastAPI server for OpenEnv HuggingFace Space deployment
"""
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Any, Dict, Optional
import uvicorn

from environment import ScamDetectionEnv
from tasks import get_all_tasks

app = FastAPI(
    title="Scam Detection OpenEnv",
    description="AI Scam & Impersonation Detection Environment for Content Moderation",
    version="1.0.0"
)

# Global environment instance
current_env = None
current_task_index = 0


class StepRequest(BaseModel):
    action: str


class StepResponse(BaseModel):
    observation: Dict[str, Any]
    reward: float
    done: bool
    info: Dict[str, Any]


@app.get("/")
def root():
    """Health check endpoint - required for HF Space validation"""
    return {
        "status": "ok",
        "environment": "Scam Detection OpenEnv",
        "version": "1.0.0",
        "tasks": len(get_all_tasks()),
        "real_world_task": "content_moderation"
    }


@app.post("/reset")
def reset(task_index: Optional[int] = 0):
    """
    Reset environment to initial state

    Args:
        task_index: Index of task to load (0=easy, 1=medium, 2=hard)

    Returns:
        Initial observation and task metadata
    """
    global current_env, current_task_index

    tasks = get_all_tasks()
    if task_index < 0 or task_index >= len(tasks):
        raise HTTPException(
            status_code=400,
            detail=f"Invalid task_index. Must be 0-{len(tasks)-1}"
        )

    current_task_index = task_index
    task = tasks[current_task_index]
    current_env = ScamDetectionEnv(task)

    observation = current_env.reset()

    return {
        "observation": observation.dict(),
        "task_name": task["name"],
        "task_difficulty": task["difficulty"],
        "task_description": task["description"]
    }


@app.post("/step", response_model=StepResponse)
def step(request: StepRequest):
    """
    Execute one step in the environment

    Args:
        request: StepRequest containing action string

    Returns:
        StepResponse with observation, reward, done, info
    """
    global current_env

    if current_env is None:
        raise HTTPException(
            status_code=400,
            detail="Environment not initialized. Call /reset first"
        )

    obs, reward, done, info = current_env.step(request.action)

    return StepResponse(
        observation=obs.dict(),
        reward=float(reward),
        done=done,
        info=info
    )


@app.get("/state")
def state():
    """Get current environment state"""
    global current_env

    if current_env is None:
        raise HTTPException(
            status_code=400,
            detail="Environment not initialized. Call /reset first"
        )

    return current_env.state()


@app.get("/tasks")
def list_tasks():
    """List all available tasks with metadata"""
    tasks = get_all_tasks()
    return {
        "count": len(tasks),
        "tasks": [
            {
                "index": i,
                "name": task["name"],
                "difficulty": task["difficulty"],
                "description": task["description"],
                "expected_classification": task["expected_classification"],
                "expected_decision": task["expected_decision"]
            }
            for i, task in enumerate(tasks)
        ]
    }


@app.get("/info")
def environment_info():
    """Get environment metadata for OpenEnv validation"""
    return {
        "name": "scam-detection-env",
        "version": "1.0.0",
        "description": "Content moderation environment for scam and impersonation detection",
        "action_space": {
            "type": "text",
            "format": "function_call",
            "actions": [
                "classify('scam'|'impersonation'|'safe')",
                "decide('allow'|'remove'|'flag'|'escalate')",
                "reason('explanation')"
            ]
        },
        "observation_space": {
            "type": "dict",
            "fields": {
                "step_type": "str (classify|decide|reason)",
                "content": "str",
                "previous_classification": "str | None",
                "previous_decision": "str | None",
                "message": "str"
            }
        },
        "reward_range": [-1.0, 1.0],
        "episode_length": "variable (1-3 steps)",
        "tasks": len(get_all_tasks())
    }


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=7860)
