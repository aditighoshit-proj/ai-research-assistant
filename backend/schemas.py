"""Data contracts for Part 1. The NEXT stage (Research Planner) consumes Part1Result.decomposition.
Changing this file affects every collaborator: open a PR and tag the team."""
from typing import List, Literal, Optional
from pydantic import BaseModel, Field

InfoType = Literal["factual", "statistical", "case_study", "technical", "opinion", "comparison"]

# ---- Stage 1: Question Analyzer ----
class QuestionAnalysis(BaseModel):
    researchable: bool = True        # False -> stop and show `reason`
    reason: str = ""
    intent: str = ""
    scope: str = ""
    key_concepts: List[str] = []
    ambiguities: List[str] = []
    assumptions: List[str] = []

# ---- Stage 2: Decomposer ----
class SubQuestion(BaseModel):
    id: str                          # "SQ1"
    question: str
    info_type: InfoType              # what KIND of evidence answers it
    rationale: str = ""

class Decomposition(BaseModel):
    sub_questions: List[SubQuestion] = Field(min_length=3, max_length=6)

# ---- API response / hand-off to Part 2 ----
class Part1Result(BaseModel):
    question: str
    status: Literal["ok", "not_researchable"]
    prompt_version: str
    analysis: QuestionAnalysis
    decomposition: Optional[Decomposition] = None
    warnings: List[str] = []
    mock: bool = False               # True = canned demo output, not from an LLM
