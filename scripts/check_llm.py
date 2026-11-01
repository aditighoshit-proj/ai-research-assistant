"""Diagnose LLM setup.   python -m scripts.check_llm"""
import os
from backend.llm import call_llm, model_name

key = os.getenv("LLM_API_KEY") or ""
print("LLM_API_KEY :", (key[:6] + "..." + key[-4:]) if len(key) > 12 else ("(not set)" if not key else "(set, very short)"))
print("LLM_BASE_URL:", os.getenv("LLM_BASE_URL") or "(empty = OpenAI default https://api.openai.com/v1)")
print("LLM_MODEL   :", model_name())
print("LLM_MOCK    :", os.getenv("LLM_MOCK", "0"))
try:
    print("Reply       :", call_llm("You are a helpful assistant.", "Reply with exactly: OK"))
    print("\nSUCCESS: the provider accepted the key, base URL and model.")
except Exception as e:
    print("\nFAILED:", e)
