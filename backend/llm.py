"""Single LLM wrapper. Every stage calls this; never call the API directly elsewhere."""
import json, os, re, time
from pathlib import Path
from typing import List, Type, TypeVar
from dotenv import load_dotenv
from openai import APIStatusError, OpenAI
from pydantic import BaseModel, ValidationError

load_dotenv()
T = TypeVar("T", bound=BaseModel)
PROMPTS_DIR = Path(__file__).parent / "prompts"
_client = None

def model_name() -> str:
    return os.getenv("LLM_MODEL", "gpt-4o-mini")

def is_mock() -> bool:
    return os.getenv("LLM_MOCK", "0") == "1"

def _get_client() -> OpenAI:
    global _client
    if _client is None:
        key = os.getenv("LLM_API_KEY")
        if not key:
            raise RuntimeError("LLM_API_KEY is not set. Add it to .env (or set LLM_MOCK=1 for demo output).")
        _client = OpenAI(api_key=key, base_url=os.getenv("LLM_BASE_URL") or None)
    return _client

def _explain(e: APIStatusError) -> str:
    body = (getattr(e.response, "text", "") or "").strip()[:300]
    return (f"The LLM provider rejected the request (HTTP {e.status_code}). Provider said: {body or e.message}. "
            f"Check LLM_API_KEY, LLM_BASE_URL and LLM_MODEL in .env "
            f"(now: model={model_name()}, base_url={os.getenv('LLM_BASE_URL') or 'OpenAI default'}). "
            f"Run: python -m scripts.check_llm")

def call_llm(system: str, user: str, temperature: float = 0.0, retries: int = 3) -> str:
    last = None
    for attempt in range(retries):
        try:
            r = _get_client().chat.completions.create(
                model=model_name(), temperature=temperature,
                messages=[{"role": "system", "content": system}, {"role": "user", "content": user}])
            return r.choices[0].message.content or ""
        except RuntimeError:
            raise                      # missing key: retrying will not help
        except APIStatusError as e:
            if e.status_code in (400, 401, 403, 404):   # configuration problem: retrying cannot fix it
                raise RuntimeError(_explain(e)) from e
            last = e                                    # 429 / 5xx: worth retrying
            time.sleep(2 ** attempt)
        except Exception as e:
            last = e
            time.sleep(2 ** attempt)
    raise RuntimeError(f"LLM call failed after {retries} tries: {last}")

def _extract_json(text: str) -> dict:
    text = re.sub(r"^```(?:json)?|```$", "", text.strip(), flags=re.M).strip()
    return json.loads(text[text.find("{"): text.rfind("}") + 1])

def call_json(system: str, user: str, model_cls: Type[T], retries: int = 3) -> T:
    """LLM call -> parse JSON -> validate with Pydantic. On failure retry with the error fed back."""
    if is_mock():
        from .mock import mock_response
        return mock_response(model_cls)
    prompt = user
    for _ in range(retries):
        raw = call_llm(system, prompt)
        try:
            return model_cls.model_validate(_extract_json(raw))
        except (json.JSONDecodeError, ValidationError, ValueError) as e:
            prompt = f"{user}\n\nYour previous reply was invalid: {e}\nReturn ONLY valid JSON."
    raise RuntimeError(f"No valid {model_cls.__name__} after {retries} tries")

def list_versions() -> List[str]:
    return sorted(p.name for p in PROMPTS_DIR.iterdir() if p.is_dir())

def load_prompt(name: str, version: str = "final") -> str:
    if version not in list_versions():
        raise ValueError(f"Unknown prompt version: {version}")
    return (PROMPTS_DIR / version / f"{name}.txt").read_text(encoding="utf-8")
