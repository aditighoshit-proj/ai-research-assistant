# AI Research Assistant: Part 1 (Research Question → Sub-questions)

Part 1 of a group project: turn an open research question into a **structured understanding** (intent, scope, ambiguities) and **3-6 sub-questions**, each tagged with the kind of evidence needed. Frontend: HTML/CSS/JS. Backend: Python (FastAPI).

```
Research Question → [Understand] → [Break into sub-questions] → JSON hand-off → (Research Plan → Analysis → Findings → Gaps → Brief)
                    └──────────── this repo ────────────────┘   └──────────── other collaborators ────────────┘
```

## Problem statement and our understanding
A user asks something like *"What are the major challenges companies face when deploying LLMs in production?"*. Asking an LLM to "research this" skips the real work. The first step of a good researcher is to work out what is being asked and split it into answerable parts. If this step is poor, everything downstream is incomplete. See [docs/part1-design.md](docs/part1-design.md).

## Quick start
```bash
unzip ai-research-assistant-part1.zip && cd ai-research-assistant
python -m venv .venv
source .venv/bin/activate            # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env                 # Windows: copy .env.example .env  -> add LLM_API_KEY
uvicorn backend.app:app --reload
```
Open http://localhost:8000.

No API key yet? Set `LLM_MOCK=1` in `.env` to see the UI with canned output (a banner marks it as demo mode).

Works with any OpenAI-compatible provider: set `LLM_BASE_URL` and `LLM_MODEL` in `.env`.

```bash
pytest -q                                   # unit + API tests (LLM mocked, no key needed)
python -m eval.run_eval --runs 3            # real-LLM evaluation of 12 cases -> eval/results.md
```

## Troubleshooting: "LLM call failed" / HTTP 401, 403, 404
The UI is fine; the provider rejected the request. Run `python -m scripts.check_llm` to see exactly what is configured and what the provider said. Usual causes:
- **Key and base URL don't match.** Each provider needs its own `LLM_BASE_URL`:

| Provider | `LLM_BASE_URL` | `LLM_MODEL` |
|---|---|---|
| OpenAI | _(leave empty)_ | `gpt-4o-mini` |
| NVIDIA (build.nvidia.com) | `https://integrate.api.nvidia.com/v1` | model ID copied from the model's page |
| Groq | `https://api.groq.com/openai/v1` | model ID from Groq's model list |

- **Model not available to your key** (wrong name, no access, free tier): use a model ID the provider lists for your account.
- **Region / network block** (403 with an HTML or "Forbidden" body): try another network or provider.
- **After editing `.env` you must restart `uvicorn`.** `--reload` only watches `.py` files, so `.env` changes are not picked up.

## API
`POST /api/decompose`  `{"question": "...", "version": "final"}` →
```json
{
  "question": "...", "status": "ok", "prompt_version": "final", "mock": false,
  "analysis": {"researchable": true, "intent": "...", "scope": "...", "key_concepts": [], "ambiguities": [], "assumptions": []},
  "decomposition": {"sub_questions": [{"id": "SQ1", "question": "...?", "info_type": "technical", "rationale": "..."}]},
  "warnings": []
}
```
`status` is `"not_researchable"` (with `analysis.reason`, `decomposition: null`) for input that can't be researched. Other endpoints: `GET /api/health`, `GET /api/versions`.

## Repository map
| Path | What |
|---|---|
| `backend/app.py` | FastAPI app, serves the frontend |
| `backend/stages/analyze.py`, `decompose.py` | The two stages |
| `backend/rules.py` | Code checks on the decomposition |
| `backend/schemas.py` | **Data contract** shared with the next stage |
| `backend/llm.py` | Single LLM wrapper (JSON parse, validation, retries, mock mode) |
| `backend/prompts/{v1,v2,final}/` | Prompt versions |
| `frontend/` | `index.html`, `style.css`, `app.js` (no build step) |
| `eval/` | 12 test cases + runner |
| `docs/part1-design.md` | Architecture diagram, LLM-vs-code decisions, trade-offs |
| `docs/prompt-engineering.md` | Prompt V1 → V2 → final log (fill in with real runs) |
| `tests/` | pytest suite |

## For the next collaborators
Take `Part1Result.decomposition.sub_questions` (+ `analysis.scope` / `assumptions`) as input for the Research Planner. Add your stage under `backend/stages/`, extend `backend/pipeline.py`, and add your schemas to `backend/schemas.py` via PR. Don't edit old prompt versions: copy to a new folder and log the change.

## Team
| Name | Role |
|---|---|
| Adi | Collaborator 1: Part 1 (question analysis + decomposition, frontend, backend scaffold) |
| _TODO_ | |

## AI usage, demo, live URL
_TODO: document AI tool usage, add screenshots of the UI, add live URL if deployed._
