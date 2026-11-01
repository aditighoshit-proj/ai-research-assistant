"""Canned output so the frontend can be developed and demoed without an API key (LLM_MOCK=1).
It ignores the question on purpose; the UI shows a banner whenever it is active."""
from .schemas import Decomposition, QuestionAnalysis, SubQuestion

def mock_response(model_cls):
    if model_cls is QuestionAnalysis:
        return QuestionAnalysis(
            researchable=True,
            intent="DEMO: understand the main obstacles organisations meet when putting the technology into real use.",
            scope="DEMO: organisations moving from prototype to production; excludes academic research settings.",
            key_concepts=["demo concept A", "demo concept B", "production"],
            ambiguities=["What counts as 'production' (internal tool vs customer-facing)?"],
            assumptions=["Production means a system used by real users or staff on a regular basis."])
    if model_cls is Decomposition:
        return Decomposition(sub_questions=[
            SubQuestion(id="SQ1", info_type="technical",
                        question="DEMO: What technical obstacles appear when moving a prototype into production?",
                        rationale="Core engineering difficulties."),
            SubQuestion(id="SQ2", info_type="statistical",
                        question="DEMO: How much does operating the system cost at scale, and what drives that cost?",
                        rationale="Cost is a common blocker and is usually reported with numbers."),
            SubQuestion(id="SQ3", info_type="case_study",
                        question="DEMO: Which organisations hit problems after launch, and how did they respond?",
                        rationale="Real examples show how issues play out."),
            SubQuestion(id="SQ4", info_type="opinion",
                        question="DEMO: What practices do experts recommend for reducing deployment risk?",
                        rationale="Collects recommended mitigations.")])
    raise ValueError(f"No mock for {model_cls}")
