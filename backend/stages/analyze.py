"""Stage 1: Question Analyzer. Input check (code) + understanding (LLM)."""
from ..llm import call_json, load_prompt
from ..schemas import QuestionAnalysis

MIN_WORDS = 3
MAX_CHARS = 1000

def analyze_question(question: str, version: str = "final") -> QuestionAnalysis:
    q = " ".join(question.split())          # normalise whitespace
    # Rules first: cheap, deterministic, no LLM call wasted
    if len(q.split()) < MIN_WORDS:
        return QuestionAnalysis(researchable=False,
                                reason=f"Input is too short to be a research question (needs at least {MIN_WORDS} words).")
    if len(q) > MAX_CHARS:
        return QuestionAnalysis(researchable=False,
                                reason=f"Input is longer than {MAX_CHARS} characters; please state one focused question.")
    # LLM: intent, scope, ambiguities (and rejection of non-research input)
    return call_json(load_prompt("analyze", version), f"Research question:\n{q}", QuestionAnalysis)
