"""Stage 2: Decomposer. LLM proposes 3-6 sub-questions; code validates; retry loop with feedback."""
import logging
from ..llm import call_json, load_prompt
from ..rules import check_decomposition
from ..schemas import Decomposition, QuestionAnalysis

log = logging.getLogger(__name__)

def decompose(question: str, analysis: QuestionAnalysis, version: str = "final", max_attempts: int = 3) -> Decomposition:
    if not analysis.researchable:
        raise ValueError(f"Cannot decompose: {analysis.reason}")
    system = load_prompt("decompose", version)
    base = f"Research question:\n{' '.join(question.split())}\n\nAnalysis:\n{analysis.model_dump_json(indent=2)}"
    user, errors = base, []
    for attempt in range(1, max_attempts + 1):
        d = call_json(system, user, Decomposition)           # schema check: 3-6 items, valid info_type
        errors, warnings = check_decomposition(d, analysis)   # rule check: ids, length, duplicates
        for w in warnings:
            log.warning("decompose warning: %s", w)
        if not errors:
            return d
        log.info("decompose attempt %d rejected: %s", attempt, errors)
        user = (base + "\n\nYour previous answer had these problems. Fix them and return the full JSON again:\n"
                + "\n".join(f"- {e}" for e in errors))
    raise ValueError("Decomposition failed validation: " + "; ".join(errors))
