"""
OpenEnv-compliant FastAPI + Gradio Server
Supports both /reset, /step, /state API endpoints AND Gradio UI
"""
import sys
import os
# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import gradio as gr
from fastapi import FastAPI
from typing import Optional, Dict, Any
from pydantic import BaseModel

from environment import ScamDetectionEnv
from tasks import get_all_tasks
from models import Observation

# ========================
# FastAPI Application
# ========================

app = FastAPI(
    title="Scam Detection OpenEnv",
    description="Content Moderation Environment for AI Agent Training",
    version="1.0.0"
)

# ========================
# Global State
# ========================

current_env = None
current_task_index = 0

current_state = {
    "task_index": 0,
    "observation": None,
    "done": False,
    "total_reward": 0.0,
    "step_count": 0,
}

# ========================
# FastAPI Request/Response Models
# ========================

class StepRequest(BaseModel):
    action: str

class ResetResponse(BaseModel):
    observation: Dict[str, Any]

class StepResponse(BaseModel):
    observation: Dict[str, Any]
    reward: float
    done: bool
    info: Dict[str, Any]

class StateResponse(BaseModel):
    task_index: int
    step_count: int
    done: bool
    total_reward: float

# ========================
# FastAPI Endpoints (OpenEnv Spec)
# ========================

@app.get("/")
async def root():
    """Health check endpoint"""
    return {
        "status": "ok",
        "environment": "Scam Detection OpenEnv",
        "version": "1.0.0",
        "spec": "openenv",
        "tasks": len(get_all_tasks())
    }

@app.post("/reset", response_model=ResetResponse)
async def api_reset(task_index: int = 0):
    """Reset environment to initial state"""
    global current_env, current_task_index, current_state
    
    tasks = get_all_tasks()
    if task_index < 0 or task_index >= len(tasks):
        return {"error": f"Invalid task_index. Must be 0-{len(tasks)-1}"}
    
    current_env = ScamDetectionEnv(tasks[task_index])
    current_task_index = task_index
    observation = current_env.reset()
    
    current_state["task_index"] = task_index
    current_state["observation"] = observation
    current_state["done"] = False
    current_state["total_reward"] = 0.0
    current_state["step_count"] = 0
    
    # Convert Observation model to dict
    if hasattr(observation, 'model_dump'):
        obs_dict = observation.model_dump()
    elif hasattr(observation, 'dict'):
        obs_dict = observation.dict()
    else:
        obs_dict = dict(observation)
    
    return {"observation": obs_dict}

@app.post("/step", response_model=StepResponse)
async def api_step(request: StepRequest):
    """Execute one step in the environment"""
    global current_env, current_state
    
    if current_env is None:
        return {
            "observation": {},
            "reward": 0.0,
            "done": True,
            "info": {"error": "Environment not initialized. Call /reset first."}
        }
    
    observation, reward, done, info = current_env.step(request.action)
    
    current_state["observation"] = observation
    current_state["done"] = done
    current_state["total_reward"] += reward
    current_state["step_count"] += 1
    
    # Convert Observation model to dict
    if hasattr(observation, 'model_dump'):
        obs_dict = observation.model_dump()
    elif hasattr(observation, 'dict'):
        obs_dict = observation.dict()
    else:
        obs_dict = dict(observation)
    
    return {
        "observation": obs_dict,
        "reward": reward,
        "done": done,
        "info": info
    }

@app.get("/state", response_model=StateResponse)
async def api_state():
    """Get current environment state"""
    return {
        "task_index": current_state["task_index"],
        "step_count": current_state["step_count"],
        "done": current_state["done"],
        "total_reward": current_state["total_reward"]
    }

@app.get("/tasks")
async def api_tasks():
    """List all available tasks"""
    tasks = get_all_tasks()
    return {
        "tasks": [
            {
                "index": i,
                "difficulty": task.get("difficulty", "unknown"),
                "content": task.get("content", "")[:100] + "..."
            }
            for i, task in enumerate(tasks)
        ]
    }

# ========================
# Gradio Functions (for UI)
# ========================

def reset_env_ui(task_index: int):
    """Reset environment (Gradio UI version)"""
    global current_env, current_task_index, current_state

    try:
        tasks = get_all_tasks()
        if task_index < 0 or task_index >= len(tasks):
            return f"❌ Error: Invalid task_index. Must be 0-{len(tasks)-1}", 0, 0.0

        current_env = ScamDetectionEnv(tasks[task_index])
        current_task_index = task_index
        observation = current_env.reset()

        current_state["task_index"] = task_index
        current_state["observation"] = observation
        current_state["done"] = False
        current_state["total_reward"] = 0.0
        current_state["step_count"] = 0

        obs_text = format_observation(observation)
        return f"✅ Environment Reset\n\nTask: {task_index}\n\n{obs_text}", current_state["step_count"], current_state["total_reward"]

    except Exception as e:
        return f"❌ Error: {str(e)}", 0, 0.0


def step_env_ui(action: str):
    """Execute one step (Gradio UI version)"""
    global current_env, current_state

    if current_env is None or current_state["observation"] is None:
        return "⚠️ Environment not initialized. Click 'Reset Environment' first.", current_state["step_count"], current_state["total_reward"]

    try:
        observation, reward, done, info = current_env.step(action)

        current_state["observation"] = observation
        current_state["done"] = done
        current_state["total_reward"] += reward
        current_state["step_count"] += 1

        obs_text = format_observation(observation)
        reward_str = f"Last Reward: {reward:.2f}\nTotal Reward: {current_state['total_reward']:.2f}"

        if done:
            result = f"🎯 Episode Complete!\n\n{obs_text}\n\n{reward_str}\n\n✨ Final Score: {current_state['total_reward']:.2f}"
        else:
            result = f"✅ Step Executed\n\n{obs_text}\n\n{reward_str}"

        return result, current_state["step_count"], current_state["total_reward"]

    except Exception as e:
        return f"❌ Error: {str(e)}", current_state["step_count"], current_state["total_reward"]


def format_observation(obs):
    """Format observation for display"""
    if hasattr(obs, 'model_dump'):
        obs_dict = obs.model_dump()
    elif hasattr(obs, 'dict'):
        obs_dict = obs.dict()
    elif isinstance(obs, dict):
        obs_dict = obs
    else:
        return str(obs)
    
    lines = []
    for key, value in obs_dict.items():
        if isinstance(value, str) and len(value) > 100:
            lines.append(f"**{key}:**\n{value[:100]}...")
        else:
            lines.append(f"**{key}:** {value}")
    return "\n\n".join(lines)


# ========================
# Gradio Interface
# ========================

def create_gradio_demo():
    """Create Gradio interface"""
    with gr.Blocks(title="Scam Detection OpenEnv", theme=gr.themes.Soft()) as demo:
        gr.Markdown("""
        # 🛡️ Scam Detection OpenEnv

        **Content Moderation AI Environment for Agent Training & Evaluation**

        Train RL agents to detect and respond to scams and inappropriate content.
        """)

        with gr.Row():
            with gr.Column(scale=1):
                task_selector = gr.Radio(
                    choices=["Easy (0)", "Medium (1)", "Hard (2)"],
                    value="Easy (0)",
                    label="📊 Task Difficulty",
                    info="Choose difficulty level"
                )
                reset_btn = gr.Button("🔄 Reset Environment", size="lg", variant="primary")

            with gr.Column(scale=2):
                gr.Markdown("### 📈 Environment Stats")
                step_counter = gr.Number(value=0, interactive=False, label="Steps Taken", precision=0)
                reward_counter = gr.Number(value=0.0, interactive=False, label="Total Reward")

        gr.Markdown("---")
        gr.Markdown("### ⚙️ Execute Action")

        action_input = gr.Textbox(
            label="Action Command",
            placeholder="e.g., classify('scam') or decide('remove') or reason('This looks suspicious...')",
            lines=2
        )
        step_btn = gr.Button("▶️ Execute Step", size="lg", variant="primary")

        gr.Markdown("### 📋 Observation & Feedback")
        output_display = gr.Textbox(
            label="Environment Response",
            interactive=False,
            lines=12,
            value="Environment not initialized. Click 'Reset Environment' to start."
        )

        # Connect buttons
        reset_btn.click(
            fn=lambda task: reset_env_ui(int(task.split("(")[1].split(")")[0])),
            inputs=[task_selector],
            outputs=[output_display, step_counter, reward_counter]
        )

        step_btn.click(
            fn=step_env_ui,
            inputs=[action_input],
            outputs=[output_display, step_counter, reward_counter]
        )

        gr.Markdown("""
        ---
        ### 📖 Usage Guide

        1. **Select Task**: Choose difficulty level (Easy/Medium/Hard)
        2. **Reset**: Click to initialize the environment
        3. **Execute**: Type actions and click Execute Step
        4. **Repeat**: Continue until episode is complete

        ### 🎯 Example Actions
        ```
        classify('scam')
        decide('remove')
        reason('This appears to be a phishing attempt because...')
        ```

        ### 💡 Tips
        - Complete classifications reward full points
        - Provide reasoning for context understanding
        - The environment adapts difficulty based on your actions
        """)

    return demo


# ========================
# Application Entry Point
# ========================

def main():
    """Main entry point for the server"""
    import uvicorn
    
    print("🚀 Starting Scam Detection OpenEnv...")
    print("📍 FastAPI endpoints: http://0.0.0.0:7860")
    print("📍 Gradio UI will be available at: http://0.0.0.0:7860")
    
    # Create Gradio interface
    demo = create_gradio_demo()
    
    # Mount Gradio on FastAPI
    global app
    app = gr.mount_gradio_app(app, demo, path="/")
    
    # Run server
    uvicorn.run(app, host="0.0.0.0", port=7860)


if __name__ == "__main__":
    main()
