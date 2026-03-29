# Project Architecture

## Overview

This is an OpenEnv-compliant environment for AI scam detection with a multi-step interaction model.

## File Structure

```
scam_detector/
├── Core Environment
│   ├── environment.py       # Main OpenEnv implementation
│   ├── models.py           # Pydantic data models
│   └── openenv.yaml        # Environment specification
│
├── Tasks
│   ├── tasks/__init__.py   # Task loader
│   ├── tasks/easy.py       # Easy difficulty task
│   ├── tasks/medium.py     # Medium difficulty task
│   └── tasks/hard.py       # Hard difficulty task
│
├── Grading
│   ├── graders/__init__.py
│   └── graders/grader.py   # Deterministic grading logic
│
├── Inference
│   ├── inference.py        # LLM agent runner
│   ├── test_env.py         # Unit tests
│   └── example.py          # Manual examples
│
├── Configuration
│   ├── requirements.txt    # Python dependencies
│   ├── Dockerfile          # Container configuration
│   └── .gitignore          # Git ignore rules
│
└── Documentation
    ├── README.md           # Main documentation
    ├── QUICKSTART.md       # Quick start guide
    └── ARCHITECTURE.md     # This file
```

## Component Details

### 1. Models (`models.py`)

**Observation**
- `step_type`: Current step ("classify", "decide", "reason")
- `content`: Content to moderate
- `previous_classification`: Classification from step 1
- `previous_decision`: Decision from step 2
- `message`: Instruction for current step

**Action**
- `action_type`: Type of action ("classify", "decide", "reason", "noop")
- `value`: Action value (e.g., "scam", "remove", "reasoning text")
- `parse_action()`: Parses function-call strings into Action objects

**Reward**
- `total`: Total reward for the step
- `classification_score`: Score for classification
- `decision_score`: Score for decision
- `reasoning_score`: Score for reasoning
- `correct`: Whether action was correct

### 2. Environment (`environment.py`)

**ScamDetectionEnv**

Implements OpenEnv specification:

```python
class ScamDetectionEnv:
    def reset() -> Observation
    def step(action: str) -> Tuple[Observation, float, bool, Dict]
    def state() -> Dict[str, Any]
    def render() -> str
```

**Episode Flow:**
1. **Reset**: Initialize environment, return classify observation
2. **Step 1**: Agent classifies → receive decide observation
3. **Step 2**: Agent decides → receive reason observation
4. **Step 3**: Agent reasons → episode ends
5. **Done**: Return final grade

**Reward System:**
- Correct action at each step: positive reward
- Incorrect action: -0.2 penalty
- Reasoning: proportional to keyword matches

### 3. Tasks (`tasks/`)

Each task file defines:
```python
TASK = {
    "name": str,                           # Unique task identifier
    "difficulty": str,                     # easy/medium/hard
    "content": str,                        # Content to moderate
    "expected_classification": str,        # Expected classification
    "expected_decision": str,              # Expected decision
    "expected_reasoning_keywords": list,   # Keywords for reasoning
    "description": str                     # Task description
}
```

**Easy Task**: Obvious phishing scam
**Medium Task**: Celebrity impersonation scam
**Hard Task**: Subtle professional phishing

### 4. Grading (`graders/grader.py`)

**ScamDetectionGrader**

Deterministic grading with three methods:

```python
def grade_classification(classification: str) -> float:
    # Returns 1.0 if exact match, 0.0 otherwise

def grade_decision(decision: str) -> float:
    # Returns 1.0 if exact match, 0.0 otherwise

def grade_reasoning(reasoning: str) -> float:
    # Returns 0.0-1.0 based on keyword matches

def grade_episode(...) -> Dict[str, float]:
    # Returns weighted total score
```

**Scoring Formula:**
```
total = (classification * 0.3) + (decision * 0.4) + (reasoning * 0.3)
```

### 5. Inference (`inference.py`)

**LLMAgent**

OpenAI-compatible client that:
1. Takes observations as input
2. Builds appropriate prompts per step
3. Calls LLM API
4. Returns parsed actions

**Flow:**
```
For each task:
    1. Create environment
    2. Reset environment
    3. While not done and steps < max:
        a. Get observation
        b. Build prompt for current step
        c. Call LLM
        d. Parse action
        e. Execute step
        f. Collect rewards
    4. Display final grade
```

## Data Flow

```
┌─────────────┐
│   Task      │ (content + expected values)
└──────┬──────┘
       │
       v
┌─────────────┐
│   Grader    │ (stores expected values)
└──────┬──────┘
       │
       v
┌──────────────────────────────────────────┐
│           Environment                    │
│  ┌────────────────────────────────────┐ │
│  │ Step 1: Classify                   │ │
│  │  Input: Content                    │ │
│  │  Output: classify('scam')          │ │
│  │  Reward: 0.3 if correct           │ │
│  └────────────────────────────────────┘ │
│  ┌────────────────────────────────────┐ │
│  │ Step 2: Decide                     │ │
│  │  Input: Content + Classification   │ │
│  │  Output: decide('remove')          │ │
│  │  Reward: 0.4 if correct           │ │
│  └────────────────────────────────────┘ │
│  ┌────────────────────────────────────┐ │
│  │ Step 3: Reason                     │ │
│  │  Input: Content + Classification   │ │
│  │         + Decision                 │ │
│  │  Output: reason('explanation')     │ │
│  │  Reward: 0.0-0.3 based on keywords│ │
│  └────────────────────────────────────┘ │
└──────────────────────────────────────────┘
       │
       v
┌─────────────┐
│  Final      │ (total score, breakdown)
│  Grade      │
└─────────────┘
```

## Action Parsing

The system uses regex to parse function-call formatted actions:

```python
# Input: "classify('scam')"
# Pattern: classify\(['\"](.+?)['\"]\)
# Output: Action(action_type="classify", value="scam")

# Input: "decide('remove')"
# Pattern: decide\(['\"](.+?)['\"]\)
# Output: Action(action_type="decide", value="remove")

# Input: "reason('This is phishing')"
# Pattern: reason\(['\"](.+?)['\"]\)
# Output: Action(action_type="reason", value="This is phishing")

# Input: anything else
# Output: Action(action_type="noop", value="")
```

## Reward Calculation

### Step-by-Step Rewards

**Step 1 (Classify):**
```python
if classification == expected_classification:
    reward = 0.3
else:
    reward = -0.2
```

**Step 2 (Decide):**
```python
if decision == expected_decision:
    reward = 0.4
else:
    reward = -0.2
```

**Step 3 (Reason):**
```python
matched_keywords = count_matched_keywords(reasoning, expected_keywords)
keyword_score = matched_keywords / len(expected_keywords)
if keyword_score > 0:
    reward = 0.3 * keyword_score
else:
    reward = -0.2
```

### Final Episode Score

```python
final_score = (
    classification_score * 0.3 +
    decision_score * 0.4 +
    reasoning_score * 0.3
)
```

Range: **0.0 to 1.0**

## Extension Points

### 1. Add New Tasks

Create new file in `tasks/` following the TASK dictionary format.

### 2. Modify Grading

Adjust weights in `graders/grader.py`:
- Change classification weight (currently 0.3)
- Change decision weight (currently 0.4)
- Change reasoning weight (currently 0.3)

### 3. Add New Actions

Modify `models.py` to parse new action formats.

### 4. Change Reward Structure

Modify `environment.py` step() method to adjust rewards.

### 5. Add More Steps

Increase `max_steps` and add new step types in `environment.py`.

## Testing

### Unit Tests (`test_env.py`)
Tests basic environment functionality without LLM.

### Manual Examples (`example.py`)
Runs all tasks with perfect answers to verify grading.

### Integration Tests (`inference.py`)
Full end-to-end test with LLM agent.

## Docker Deployment

**Build:**
```bash
docker build -t scam-detector .
```

**Run:**
```bash
docker run -e OPENAI_API_KEY=... scam-detector
```

The Dockerfile:
1. Uses Python 3.11-slim base image
2. Installs dependencies from requirements.txt
3. Copies application code
4. Sets environment variables
5. Runs inference.py

## Performance Expectations

| Task | Difficulty | Perfect Score | Good Score | Minimum Passing |
|------|-----------|--------------|------------|-----------------|
| Easy | Easy | 1.0 | 0.85+ | 0.70 |
| Medium | Medium | 1.0 | 0.80+ | 0.65 |
| Hard | Hard | 1.0 | 0.75+ | 0.60 |

## Key Design Decisions

1. **Multi-Step Episodes**: Forces sequential reasoning (classify → decide → reason)
2. **Function-Call Format**: Makes action parsing reliable and structured
3. **Deterministic Grading**: Ensures reproducible evaluation
4. **Partial Credit**: Rewards partial correctness in reasoning
5. **Step-by-Step Rewards**: Provides immediate feedback for learning
6. **Keyword Matching**: Simple but effective reasoning evaluation
7. **OpenEnv Compliance**: Standard interface for RL/LLM systems

## Limitations & Future Work

**Current Limitations:**
- Keyword matching for reasoning is simplistic
- Only 3 tasks included
- No semantic similarity in reasoning evaluation
- No multi-agent scenarios

**Future Enhancements:**
- Add semantic similarity scoring for reasoning
- Include more diverse tasks (deepfakes, social engineering)
- Multi-agent debate scenarios
- Dynamic task generation
- Confidence scoring
- Explanation quality metrics beyond keywords
