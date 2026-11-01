import pytest
from pydantic import ValidationError
from backend.schemas import Decomposition, QuestionAnalysis, SubQuestion
from backend.rules import check_decomposition
from backend.llm import load_prompt, list_versions
import backend.stages.analyze as analyze_mod
import backend.stages.decompose as decompose_mod

def sq(i, text, t="technical"):
    return SubQuestion(id=f"SQ{i}", question=text, info_type=t)

GOOD = Decomposition(sub_questions=[
    sq(1, "What technical difficulties arise when scaling LLM inference in production?"),
    sq(2, "How do companies control the cost of running LLM applications?", "statistical"),
    sq(3, "Which security and privacy risks affect deployed LLM systems?", "factual"),
])
DUP = Decomposition(sub_questions=[
    sq(1, "What are the cost challenges of deploying LLMs in production?"),
    sq(2, "What are the cost challenges of deploying LLMs in production environments?"),
    sq(3, "Which security risks affect deployed LLM systems?"),
])
ANALYSIS = QuestionAnalysis(intent="i", scope="s", key_concepts=["LLM", "production"])

def test_short_input_rejected_without_llm(monkeypatch):
    monkeypatch.setattr(analyze_mod, "call_json", lambda *a, **k: pytest.fail("LLM must not be called"))
    r = analyze_mod.analyze_question("hello")
    assert r.researchable is False and "short" in r.reason

def test_too_long_input_rejected(monkeypatch):
    monkeypatch.setattr(analyze_mod, "call_json", lambda *a, **k: pytest.fail("LLM must not be called"))
    assert analyze_mod.analyze_question("word " * 400).researchable is False

def test_schema_rejects_too_few_subquestions():
    with pytest.raises(ValidationError):
        Decomposition(sub_questions=[sq(1, "What is the main cost driver here?")] * 2)

def test_schema_rejects_unknown_info_type():
    with pytest.raises(ValidationError):
        SubQuestion(id="SQ1", question="What is X really about?", info_type="vibes")

def test_rules_flag_near_duplicates():
    errors, _ = check_decomposition(DUP)
    assert any("near-duplicates" in e for e in errors)

def test_rules_flag_bad_ids():
    d = Decomposition(sub_questions=[sq(1, "What technical difficulties arise when scaling inference?"),
                                     sq(3, "How do companies control the cost of applications?"),
                                     sq(4, "Which security risks affect deployed systems overall?")])
    assert any("IDs" in e for e in check_decomposition(d)[0])

def test_rules_pass_good_decomposition():
    assert check_decomposition(GOOD, ANALYSIS) == ([], [])

def test_rules_warn_on_yes_no_and_uncovered_concept():
    d = Decomposition(sub_questions=[sq(1, "Is latency a problem for chat products today?"),
                                     sq(2, "How do teams budget for GPU spending each quarter?"),
                                     sq(3, "Which security risks affect deployed systems overall?")])
    _, w = check_decomposition(d, QuestionAnalysis(key_concepts=["hallucination"]))
    assert any("yes/no" in x for x in w) and any("hallucination" in x for x in w)

def test_decompose_retries_with_feedback(monkeypatch):
    seen, replies = [], iter([DUP, GOOD])
    def fake(system, user, model):
        seen.append(user); return next(replies)
    monkeypatch.setattr(decompose_mod, "call_json", fake)
    assert decompose_mod.decompose("q about LLM production", ANALYSIS) == GOOD
    assert len(seen) == 2 and "near-duplicates" in seen[1]

def test_decompose_gives_up_after_max_attempts(monkeypatch):
    monkeypatch.setattr(decompose_mod, "call_json", lambda *a, **k: DUP)
    with pytest.raises(ValueError):
        decompose_mod.decompose("q", ANALYSIS, max_attempts=2)

def test_decompose_refuses_unresearchable():
    with pytest.raises(ValueError):
        decompose_mod.decompose("hello", QuestionAnalysis(researchable=False, reason="x"))

def test_unknown_prompt_version_rejected():
    with pytest.raises(ValueError):
        load_prompt("analyze", "../../etc")

@pytest.mark.parametrize("version", ["v1", "v2", "final"])
@pytest.mark.parametrize("name", ["analyze", "decompose"])
def test_prompts_exist_and_demand_json(version, name):
    assert version in list_versions() and "JSON" in load_prompt(name, version)


def test_403_fails_fast_with_clear_message(monkeypatch):
    import httpx, openai
    import backend.llm as llm
    calls = []
    resp = httpx.Response(403, request=httpx.Request("POST", "https://x"), text="Forbidden by gateway")
    err = openai.PermissionDeniedError("Error code: 403", response=resp, body=None)
    class FakeClient:
        class chat:
            class completions:
                @staticmethod
                def create(**k):
                    calls.append(1); raise err
    monkeypatch.setattr(llm, "_get_client", lambda: FakeClient)
    with pytest.raises(RuntimeError, match="403.*LLM_BASE_URL"):
        llm.call_llm("s", "u")
    assert len(calls) == 1          # no pointless retries
