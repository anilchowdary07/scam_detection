"""
Gradio + FastAPI Server for OpenEnv HuggingFace Space
Runs Gradio UI on port 7860 with embedded FastAPI endpoints
"""
import gradio as gr
from typing import Optional, Dict, Any
from pydantic import BaseModel

from environment import ScamDetectionEnv
from tasks import get_all_tasks

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
# Environment Functions
# ========================

def reset_env(task_index: int):
    """Reset environment to initial state"""
    global current_env, current_task_index, current_state

    try:
        tasks = get_all_tasks()
        if task_index < 0 or task_index >= len(tasks):
            return f"❌ Error: Invalid task_index. Must be 0-{len(tasks)-1}", 0, 0.0

        current_env = ScamDetectionEnv(tasks[task_index])
        current_task_index = task_index
        observation, _ = current_env.reset()

        current_state["task_index"] = task_index
        current_state["observation"] = observation
        current_state["done"] = False
        current_state["total_reward"] = 0.0
        current_state["step_count"] = 0

        obs_text = format_observation(observation)
        return f"✅ Environment Reset\n\nTask: {task_index}\n\n{obs_text}", current_state["step_count"], current_state["total_reward"]

    except Exception as e:
        return f"❌ Error: {str(e)}", 0, 0.0


def step_env(action: str):
    """Execute one step in the environment"""
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
    if isinstance(obs, dict):
        lines = []
        for key, value in obs.items():
            if isinstance(value, str) and len(value) > 100:
                lines.append(f"**{key}:**\n{value[:100]}...")
            else:
                lines.append(f"**{key}:** {value}")
        return "\n\n".join(lines)
    return str(obs)


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
            fn=lambda task: reset_env(int(task.split("(")[1].split(")")[0])),
            inputs=[task_selector],
            outputs=[output_display, step_counter, reward_counter]
        )

        step_btn.click(
            fn=step_env,
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


if __name__ == "__main__":
    print("🚀 Starting Scam Detection OpenEnv...")
    print("📍 Access at: http://0.0.0.0:7860")

    demo = create_gradio_demo()
    demo.launch(
        server_name="0.0.0.0",
        server_port=7860,
        share=False,
        show_error=True
    )
