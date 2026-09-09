import os

import httpx
from google import genai
from google.genai import types


PROVIDER = os.getenv("LLM_PROVIDER", "ollama").lower()
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://ollama:11434").rstrip("/")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama3.2:3b")
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")


def _ollama_analysis(update_text: str) -> dict[str, object]:
    prompt = f"""
You are a legal case information extraction assistant. Do not give legal advice,
predict a judge's decision, or invent facts. Extract only what is explicitly
present in this user-provided case update.

Return JSON with these fields:
event_type, event_date, stage, summary, source_ref, requires_human_review,
review_reasons.

Case update:
{update_text}
"""
    response = httpx.post(
        f"{OLLAMA_BASE_URL}/api/generate",
        json={"model": OLLAMA_MODEL, "prompt": prompt, "format": "json", "stream": False},
        timeout=120,
    )
    response.raise_for_status()
    result = response.json().get("response", "")
    return {
        "status": "ready",
        "provider": "ollama",
        "model": OLLAMA_MODEL,
        "result": result,
        "requires_human_review": True,
        "review_reasons": ["AI output requires human legal review"],
    }


def analyze_case_update(update_text: str) -> dict[str, object]:
    if PROVIDER == "ollama":
        try:
            return _ollama_analysis(update_text)
        except httpx.HTTPStatusError as error:
            return {
                "status": "provider_error",
                "provider": "ollama",
                "message": "Ollama rejected the request.",
                "provider_status_code": error.response.status_code,
                "provider_message": error.response.text[:500],
                "requires_human_review": True,
            }
        except httpx.RequestError as error:
            return {
                "status": "provider_error",
                "provider": "ollama",
                "message": "Ollama is unreachable. Confirm that the Ollama container is running.",
                "error_type": type(error).__name__,
                "requires_human_review": True,
            }
        except Exception as error:
            return {
                "status": "provider_error",
                "provider": "ollama",
                "message": "Ollama could not process the request. Pull the configured model and confirm the Ollama service is running.",
                "error_type": type(error).__name__,
                "requires_human_review": True,
            }

    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        return {
            "status": "needs_configuration",
            "message": "GEMINI_API_KEY is not configured.",
            "requires_human_review": True,
        }

    client = genai.Client(api_key=api_key)
    prompt = f"""
You are a legal case information extraction assistant. Do not give legal advice,
predict a judge's decision, or invent facts. Extract only what is explicitly
present in this user-provided case update.

Return JSON with these fields:
event_type, event_date, stage, summary, source_ref, requires_human_review,
review_reasons.

Case update:
{update_text}
"""
    try:
        response = client.models.generate_content(
            model=GEMINI_MODEL,
            contents=prompt,
            config=types.GenerateContentConfig(response_mime_type="application/json"),
        )
    except Exception as error:
        return {
            "status": "provider_error",
            "message": "Gemini could not process the request.",
            "error_type": type(error).__name__,
            "requires_human_review": True,
        }

    return {
        "status": "ready",
        "provider": "gemini",
        "model": GEMINI_MODEL,
        "result": response.text,
        "requires_human_review": True,
        "review_reasons": ["AI output requires human legal review"],
    }