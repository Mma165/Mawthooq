import json
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


ASSESSMENT_SYSTEM_RULES = """You are an evidence-grounded legal case analysis assistant for Saudi business cases.
You provide decision support only. You never give binding legal advice, never predict
a judge's decision, never submit filings, and never invent facts or legal sources.
Ground every material claim strictly in the evidence provided below. If the evidence
is insufficient, say so explicitly instead of guessing."""


def _extract_json(text: str) -> dict[str, object]:
    cleaned = text.strip()
    if cleaned.startswith("```"):
        lines = cleaned.splitlines()
        lines = [line for line in lines if not line.strip().startswith("```")]
        cleaned = "\n".join(lines).strip()
    return json.loads(cleaned)


EVIDENCE_CHUNK_CHARS = 500


def _shorten(text: object) -> str:
    content = str(text or "")
    if len(content) > EVIDENCE_CHUNK_CHARS:
        return content[:EVIDENCE_CHUNK_CHARS] + "..."
    return content


def _format_evidence(legal_evidence: list[dict[str, object]], document_evidence: list[dict[str, object]]) -> str:
    lines = []
    for chunk in legal_evidence:
        lines.append(
            f"- [legal] {chunk.get('source_id')}:p{chunk.get('page_number')} "
            f"({chunk.get('title', '')}): {_shorten(chunk.get('text', ''))}"
        )
    for chunk in document_evidence:
        lines.append(
            f"- [case-doc] {chunk.get('document_id')}:p{chunk.get('page_number')}: "
            f"{_shorten(chunk.get('text', ''))}"
        )
    return "\n".join(lines) if lines else "(no retrieved evidence)"


def _call_model(prompt: str) -> tuple[str, str, str]:
    """Return (provider, model, raw_text) or raise RuntimeError on provider failure."""
    if PROVIDER == "ollama":
        try:
            response = httpx.post(
                f"{OLLAMA_BASE_URL}/api/generate",
                json={"model": OLLAMA_MODEL, "prompt": prompt, "format": "json", "stream": False},
                timeout=180,
            )
            response.raise_for_status()
            return "ollama", OLLAMA_MODEL, response.json().get("response", "")
        except Exception as error:
            raise RuntimeError(f"Ollama generation failed: {type(error).__name__}") from error
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise RuntimeError("GEMINI_API_KEY is not configured.")
    try:
        client = genai.Client(api_key=api_key)
        response = client.models.generate_content(
            model=GEMINI_MODEL,
            contents=prompt,
            config=types.GenerateContentConfig(response_mime_type="application/json"),
        )
        return "gemini", GEMINI_MODEL, response.text
    except Exception as error:
        raise RuntimeError(f"Gemini generation failed: {type(error).__name__}") from error


def generate_case_assessment(
    case: dict[str, object],
    legal_evidence: list[dict[str, object]],
    document_evidence: list[dict[str, object]],
) -> dict[str, object]:
    prompt = f"""{ASSESSMENT_SYSTEM_RULES}

Case type: {case.get('case_type')}
Current stage: {case.get('current_stage')}
Description: {case.get('description')}
Proposed lawyer action: {case.get('lawyer_proposed_action') or '(none provided)'}

Retrieved evidence:
{_format_evidence(legal_evidence, document_evidence)}

Return strict JSON with exactly these fields:
{{
  "summary": "short factual summary grounded in the case and evidence",
  "what_happens_next": [{{"text": "...", "citations": ["source-id:pN"]}}],
  "risks": ["..."],
  "recommended_lawyer_questions": ["..."],
  "citations": [{{"source_id": "...", "location": "page N", "quote": "..."}}]
}}"""
    provider, model, raw_text = _call_model(prompt)
    try:
        parsed = _extract_json(raw_text)
    except (json.JSONDecodeError, ValueError, AttributeError):
        parsed = {
            "summary": raw_text[:2000] if isinstance(raw_text, str) else "",
            "what_happens_next": [],
            "risks": ["The model output could not be parsed; verify everything with a lawyer."],
            "recommended_lawyer_questions": ["Can you verify the assessment below against the cited sources?"],
            "citations": [],
        }
    return {
        "summary": str(parsed.get("summary", "")),
        "what_happens_next": parsed.get("what_happens_next", []) or [],
        "risks": parsed.get("risks", []) or [],
        "recommended_lawyer_questions": parsed.get("recommended_lawyer_questions", []) or [],
        "citations": parsed.get("citations", []) or [],
        "provider": provider,
        "model": model,
        "requires_human_review": True,
    }


def build_case_chat_prompt(
    case: dict[str, object],
    history: list[dict[str, object]],
    user_message: str,
    legal_evidence: list[dict[str, object]],
    document_evidence: list[dict[str, object]],
) -> str:
    transcript = "\n".join(
        f"{item.get('role', 'user')}: {item.get('content', '')}" for item in history[-8:]
    )
    return f"""{ASSESSMENT_SYSTEM_RULES}

You are answering a follow-up question about one specific case. Keep the reply
concise, factual, and grounded in the evidence. Cite sources inline as
source-id:pN (for example consumer-rights-guide:p22) using ONLY the evidence
below — never invent a source id. Always remind the user to verify with their
lawyer before acting. Reply in plain text, not JSON.

Case type: {case.get('case_type')} | Current stage: {case.get('current_stage')}
Description: {case.get('description')}

Conversation so far:
{transcript if transcript else '(no prior messages)'}

User question: {user_message}

Retrieved evidence:
{_format_evidence(legal_evidence, document_evidence)}

Answer:"""


def stream_ollama_tokens(prompt: str):
    """Yield text deltas from Ollama as they are generated."""
    try:
        with httpx.stream(
            "POST",
            f"{OLLAMA_BASE_URL}/api/generate",
            json={"model": OLLAMA_MODEL, "prompt": prompt, "stream": True},
            timeout=180,
        ) as response:
            response.raise_for_status()
            for line in response.iter_lines():
                if not line:
                    continue
                try:
                    chunk = json.loads(line)
                except ValueError:
                    continue
                text = chunk.get("response", "")
                if text:
                    yield text
                if chunk.get("done"):
                    break
    except Exception as error:
        raise RuntimeError(f"Ollama stream failed: {type(error).__name__}") from error


def generate_case_chat_reply(
    case: dict[str, object],
    history: list[dict[str, object]],
    user_message: str,
    legal_evidence: list[dict[str, object]],
    document_evidence: list[dict[str, object]],
) -> dict[str, object]:
    transcript = "\n".join(
        f"{item.get('role', 'user')}: {item.get('content', '')}" for item in history[-8:]
    )
    prompt = f"""{ASSESSMENT_SYSTEM_RULES}

You are answering a follow-up question about one specific case. Keep the reply
concise, factual, and grounded in the evidence. Always remind the user to verify
with their lawyer before acting.

Case type: {case.get('case_type')} | Current stage: {case.get('current_stage')}
Description: {case.get('description')}

Conversation so far:
{transcript if transcript else '(no prior messages)'}

User question: {user_message}

Retrieved evidence:
{_format_evidence(legal_evidence, document_evidence)}

Return strict JSON with exactly these fields:
{{"reply": "your answer with inline citations like source-id:pN where relevant",
  "citations": [{{"source_id": "...", "location": "page N", "quote": "..."}}]}}"""
    provider, model, raw_text = _call_model(prompt)
    try:
        parsed = _extract_json(raw_text)
        reply = str(parsed.get("reply", "") or raw_text)
        citations = parsed.get("citations", []) or []
    except (json.JSONDecodeError, ValueError, AttributeError):
        reply = raw_text if isinstance(raw_text, str) else ""
        citations = []
    return {
        "reply": reply,
        "citations": citations,
        "provider": provider,
        "model": model,
        "requires_human_review": True,
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