# Part 1 Design: Research Question → Sub-questions

## Scope
Only the first two steps of the assignment pipeline:
```
Research Question  →  Sub-questions        (this repo)
                      ↓
        Research Plan → Information Analysis → Findings → Knowledge Gaps → Final Brief   (other collaborators)
```

## Architecture
```mermaid
flowchart LR
    U([User: browser]) -->|question + prompt version| API["FastAPI<br/>POST /api/decompose"]
    API --> G{"Input check<br/><i>code</i>"}
    G -->|too short / too long| NR([not_researchable])
    G --> A["Stage 1 Question Analyzer<br/><i>LLM</i>"]
    A -->|researchable = false| NR
    A --> D["Stage 2 Decomposer<br/><i>LLM</i>"]
    D --> V{"Rule check<br/><i>code</i>"}
    V -->|errors: duplicates, bad ids, too short| D
    V -->|ok + warnings| R([Part1Result JSON])
    R --> U
    classDef llm fill:#E8F0FE,stroke:#1A73E8; classDef code fill:#E6F4EA,stroke:#1E8E3E;
    class A,D llm; class G,V code;
```

## Where an LLM is used, and where code is used
| Step | Tool | Why |
|---|---|---|
| Input check (empty, too short, too long) | Code | Deterministic, free, no wasted LLM call |
| Understand intent, scope, ambiguities; reject non-research input | LLM | Needs language understanding |
| Generate sub-questions + evidence type | LLM | Needs judgement about dimensions of a topic |
| Schema validation (3-6 items, valid info_type) | Code (Pydantic) | Guarantees a usable structure for the next stage |
| Duplicate / ID / length checks, retry with feedback | Code | Cheap objective quality gate; LLM only retries when needed |
| Yes/no question, uncovered key concept, single info_type | Code (warnings) | Soft quality signals shown to the user and scored in eval |

## How the problem was decomposed
1. Understanding and decomposing are separate calls. A decomposition built on an explicit analysis (scope, assumptions) is easier to inspect and debug than one produced in a single prompt.
2. Each sub-question carries an `info_type` so later stages know what evidence to look for (numbers vs case studies vs expert views).
3. Code, not the LLM, decides whether the result is acceptable (count, IDs, duplicates).

## Key decisions and trade-offs
- **Two LLM calls instead of one:** more latency/cost, but each step can be tested and its prompt versioned independently.
- **Rule-based retry (max 3):** bounds cost; fails loudly (HTTP 422) instead of returning bad output.
- **3-6 sub-questions:** fewer than 3 under-decomposes; more than 6 fragments a small corpus.
- **Temperature 0:** repeatable output for evaluation.
- **Mock mode (`LLM_MOCK=1`):** lets frontend work proceed without an API key; always labelled in the UI.
- **No documents used in this part:** the corpus (`data/corpus/`) is first needed at retrieval (a later stage); decomposition depends only on the question.

## Hand-off contract to the next stage
The Research Planner should consume `Part1Result.decomposition.sub_questions` (+ `analysis.scope`, `analysis.assumptions`). The JSON is defined in `backend/schemas.py`.
