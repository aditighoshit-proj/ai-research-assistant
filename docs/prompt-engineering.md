# Prompt Engineering (Part 1)

## How to log an experiment
Use the UI's "Prompt version" dropdown, or:
```bash
python -m eval.run_eval --version v1 --runs 3     # then v2, then final
```
Every UI/API run is appended to `outputs/runs.jsonl` (question, prompt version, result). Paste REAL outputs below; do not write results you did not observe.

## Stage 1: Question Analyzer
| | |
|---|---|
| **V1** | `backend/prompts/v1/analyze.txt`: one-line instruction, no rules |
| **Result** | _TODO: paste output for S1, S4, S5, S11, S12 from `eval/cases.json`_ |
| **Problem identified** | _TODO: e.g. invented ambiguities? accepts "write me a poem"? obeys the injection case?_ |
| **Improvement** | V2 adds: `researchable` gate, concrete-terms rule, no invented ambiguities, assumption per ambiguity, injection guard |
| **V2 result** | _TODO_ |
| **Final prompt** | `backend/prompts/final/analyze.txt`; why: _TODO_ |

## Stage 2: Decomposer
| | |
|---|---|
| **V1** | `backend/prompts/v1/decompose.txt`: "break into 3-6 sub-questions" |
| **Result** | _TODO: paste sub-questions for S1, S4, S6_ |
| **Problem identified** | _TODO: overlap, yes/no questions, missing dimensions, missing info types, non-English output?_ |
| **Improvement** | V2 adds: info_type definitions, distinct-dimension rule, answerable-from-documents rule, stand-alone wording, ordering, one few-shot example on a different topic, English-output rule |
| **V2 result** | _TODO_ |
| **Final prompt** | `backend/prompts/final/decompose.txt`; why: _TODO_ |

## Why code checks surround the prompts
- `analyze_question` rejects empty / too-short / too-long input before any LLM call.
- `check_decomposition` enforces IDs, minimum length and near-duplicate detection; failures are fed back to the LLM (max 3 attempts).
- Softer problems become warnings that the evaluation counts.
