# Quick Start Guide

## Running the Environment (No LLM Required)

### 1. Test the Environment
```bash
python3 test_env.py
```

### 2. Run Manual Examples
```bash
python3 example.py
```

This will run all 3 tasks with perfect answers and show you the grading.

## Running with an LLM Agent

### Prerequisites
You need an OpenAI API key or Hugging Face token.

### Option 1: OpenAI
```bash
export OPENAI_API_KEY=sk-...
export MODEL_NAME=gpt-4
python3 inference.py
```

### Option 2: Hugging Face
```bash
export API_BASE_URL=https://api-inference.huggingface.co/v1
export MODEL_NAME=meta-llama/Llama-3-8b-chat-hf
export HF_TOKEN=hf_...
python3 inference.py
```

### Option 3: Local LLM (e.g., Ollama)
```bash
export API_BASE_URL=http://localhost:11434/v1
export MODEL_NAME=llama2
export OPENAI_API_KEY=dummy
python3 inference.py
```

## Docker

### Build
```bash
docker build -t scam-detector .
```

### Run
```bash
docker run -e OPENAI_API_KEY=sk-... scam-detector
```

Or with Hugging Face:
```bash
docker run \
  -e API_BASE_URL=https://api-inference.huggingface.co/v1 \
  -e MODEL_NAME=meta-llama/Llama-3-8b-chat-hf \
  -e HF_TOKEN=hf_... \
  scam-detector
```

## Expected Output

When running with a good LLM, you should see:

```
=== Running Task: easy_scam (easy) ===

Step 1 (classify):
Action: classify('scam')
Reward: 0.30

Step 2 (decide):
Action: decide('remove')
Reward: 0.40

Step 3 (reason):
Action: reason('This is a phishing attempt...')
Reward: 0.27

--- Final Grade ---
Total Score: 0.97
  Classification: 1.00 (weight: 0.3)
  Decision: 1.00 (weight: 0.4)
  Reasoning: 0.83 (weight: 0.3)
```

## Customization

### Add a New Task

1. Create `tasks/mynew.py`:
```python
TASK = {
    "name": "mynew_task",
    "difficulty": "medium",
    "content": "Your content here...",
    "expected_classification": "scam",
    "expected_decision": "remove",
    "expected_reasoning_keywords": ["keyword1", "keyword2"],
    "description": "Description"
}
```

2. Import in `tasks/__init__.py`:
```python
from . import easy, medium, hard, mynew

ALL_TASKS = [
    easy.TASK,
    medium.TASK,
    hard.TASK,
    mynew.TASK  # Add here
]
```

### Modify Grading Weights

Edit `graders/grader.py`, line 64:
```python
total_score = (
    classification_score * 0.3 +  # Change weight
    decision_score * 0.4 +         # Change weight
    reasoning_score * 0.3          # Change weight
)
```

## Troubleshooting

**Error: "command not found: python"**
- Use `python3` instead of `python`

**Error: "No API key found"**
- Set `OPENAI_API_KEY` or `HF_TOKEN` environment variable

**Low scores on reasoning**
- The grader looks for specific keywords. Check `expected_reasoning_keywords` in task files.

**Agent outputs wrong format**
- Ensure the LLM outputs exactly: `classify('value')` with no extra text
