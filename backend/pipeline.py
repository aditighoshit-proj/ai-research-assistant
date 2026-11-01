"""Part 1 pipeline: Research Question -> Understanding -> Sub-questions."""
import json, time
from pathlib import Path
from .llm import is_mock
from .rules import check_decomposition
from .schemas import Part1Result
from .stages.analyze import analyze_question
from .stages.decompose import decompose

RUN_LOG = Path("outputs/runs.jsonl")   # every run is logged: evidence for docs/prompt-engineering.md

def run_part1(question: str, version: str = "final") -> Part1Result:
    analysis = analyze_question(question, version)
    if not analysis.researchable:
        result = Part1Result(question=question, status="not_researchable", prompt_version=version,
                             analysis=analysis, mock=is_mock())
    else:
        d = decompose(question, analysis, version)
        _, warnings = check_decomposition(d, analysis)
        result = Part1Result(question=question, status="ok", prompt_version=version, analysis=analysis,
                             decomposition=d, warnings=warnings, mock=is_mock())
    _log(result)
    return result

def _log(result: Part1Result) -> None:
    try:
        RUN_LOG.parent.mkdir(exist_ok=True)
        with open(RUN_LOG, "a", encoding="utf-8") as f:
            f.write(json.dumps({"ts": time.strftime("%Y-%m-%d %H:%M:%S"), **result.model_dump()}, ensure_ascii=False) + "\n")
    except OSError:
        pass
