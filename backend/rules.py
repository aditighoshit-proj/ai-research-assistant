"""Deterministic checks on the Decomposer output (no LLM)."""
import re
from typing import List
from .schemas import Decomposition, QuestionAnalysis

_STOP = {"the", "and", "for", "that", "with", "from", "are", "what", "how", "why", "which", "this",
         "their", "they", "when", "does", "into", "about", "over", "than", "have", "has", "can"}
_YES_NO = ("is ", "are ", "does ", "do ", "can ", "will ", "should ", "has ", "have ", "did ")

def _toks(s: str) -> set:
    return {t for t in re.findall(r"\w+", s.lower()) if t not in _STOP and len(t) > 2}

def _jaccard(a: set, b: set) -> float:
    return len(a & b) / len(a | b) if (a | b) else 0.0

def check_decomposition(d: Decomposition, analysis: QuestionAnalysis | None = None) -> tuple[List[str], List[str]]:
    """Returns (errors, warnings). Errors trigger an LLM retry with feedback; warnings are shown and scored."""
    errors: List[str] = []
    warnings: List[str] = []
    sqs = d.sub_questions
    expected = [f"SQ{i}" for i in range(1, len(sqs) + 1)]
    if [s.id for s in sqs] != expected:
        errors.append(f"IDs must be exactly {expected}, in order")
    for s in sqs:
        if len(s.question.split()) < 5:
            errors.append(f"{s.id} is too short to be a self-contained question")
        if not s.question.strip().endswith("?"):
            warnings.append(f"{s.id} does not end with a question mark")
        if s.question.strip().lower().startswith(_YES_NO):
            warnings.append(f"{s.id} looks like a yes/no question; open questions give richer evidence")
    for i, a in enumerate(sqs):
        for b in sqs[i + 1:]:
            if _jaccard(_toks(a.question), _toks(b.question)) >= 0.7:
                errors.append(f"{a.id} and {b.id} are near-duplicates; merge or differentiate them")
    if len(sqs) >= 4 and len({s.info_type for s in sqs}) == 1:
        warnings.append("All sub-questions have the same info_type; check whether other evidence types are needed")
    if analysis is not None:
        covered = set().union(*[_toks(s.question) for s in sqs])
        missing = [c for c in analysis.key_concepts if _toks(c) and not (_toks(c) & covered)]
        if missing:
            warnings.append(f"Key concepts not reflected in any sub-question: {missing}")
    return errors, warnings
