# Scam Detection OpenEnv

Real-world content moderation environment where agents detect scams/impersonation and choose moderation actions.

Built for OpenEnv evaluation with deterministic grading, partial-progress rewards, and reproducible inference logs.

## Why this environment matters

Platforms and marketplaces process huge volumes of user-generated content where scam and impersonation abuse causes direct financial harm.  
This environment models a practical moderation workflow used in production:

1. Classify content risk.
2. Decide moderation action.
3. Provide rationale for auditability.

It is designed to evaluate agent reliability, not game-playing behavior.

## OpenEnv compliance

- Typed models via Pydantic (`models.py`)
- Core API:
  - `reset() -> Observation`
  - `step(action) -> (Observation, reward, done, info)`
  - `state() -> dict`
- Spec metadata: `openenv.yaml`
- Multi-mode deployment structure:
  - `server/app.py`
  - `pyproject.toml` with script entrypoint
  - `uv.lock`

## Task suite (easy → medium → hard)

All tasks live in `tasks/` and use deterministic graders in `graders/grader.py`.

1. **easy_scam**  
   Obvious phishing message requesting credentials.  
   Expected: `classify('scam')`, `decide('remove')`.

2. **medium_impersonation**  
   Celebrity crypto giveaway impersonation.  
   Expected: `classify('impersonation')`, `decide('remove')`.

3. **hard_subtle_phishing**  
   Legitimate-looking security alert with suspicious verification link.  
   Expected: `classify('scam')`, `decide('flag')`.

## Action and observation spaces

### Observation

```json
{
  "step_type": "classify | decide | reason",
  "content": "string",
  "previous_classification": "string|null",
  "previous_decision": "string|null",
  "message": "string"
}
```

### Action format

Function-call strings:

- `classify('scam'|'impersonation'|'safe')`
- `decide('allow'|'remove'|'flag'|'escalate')`
- `reason('...')`

## Reward design (meaningful shaping)

The environment gives dense trajectory feedback (not only terminal rewards):

- Correct classification: `+0.3`
- Wrong classification: `-0.3` and early termination
- Correct decision: `+0.4`
- Wrong decision / wrong action type: negative penalties
- Reason quality: tiered partial reward (`strong > medium > weak`)
- Progressive penalties for repeated mistakes

This creates useful learning signals for both policy quality and safety behavior.

## Grading and score range

- Deterministic per-step grading and final episode breakdown.
- Weighted episode score:
  - classification `0.3`
  - decision `0.4`
  - reasoning `0.3`
- Inference output score is clamped to strict `(0,1)` bounds to satisfy validator expectations.

## API endpoints (server)

Exposed by `server/app.py`:

- `GET /` health and metadata
- `POST /reset?task_index=<0|1|2>`
- `POST /step` with JSON body `{"action":"..."}`
- `GET /state`
- `GET /tasks`

## Baseline inference

Run:

```bash
python3 inference.py
```

It emits required structured lines:

- `[START] task=... env=... model=...`
- `[STEP] step=... action=... reward=... done=... error=...`
- `[END] success=... steps=... score=... rewards=...`

## Required environment variables

For evaluator/proxy compatibility:

- `API_BASE_URL` (LLM endpoint/proxy URL)
- `MODEL_NAME` (model identifier)
- `API_KEY` (preferred by validator proxy)

Fallbacks supported:

- `OPENAI_API_KEY`
- `HF_TOKEN`

## Local setup

```bash
python3 -m pip install -r requirements.txt
python3 test_env.py
python3 test_advanced.py
python3 inference.py
```

## Docker

```bash
docker build -t scam-detection-env .
docker run -p 7860:7860 scam-detection-env
```

Then verify:

```bash
curl -s http://localhost:7860/
curl -s -X POST "http://localhost:7860/reset?task_index=0"
```

## Repository map

- `environment.py` - environment logic and reward shaping
- `models.py` - typed `Observation`/action parsing models
- `tasks/` - easy/medium/hard task definitions
- `graders/grader.py` - deterministic graders
- `inference.py` - baseline runner + required stdout protocol
- `server/app.py` - FastAPI + Gradio app for deployment
- `openenv.yaml` - OpenEnv spec metadata
- `Dockerfile` - containerized runtime

---

This project is optimized for evaluator clarity, deterministic scoring, and practical real-world moderation utility.
