import json
from datetime import datetime, timezone
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from app import services
from app.main import app


CASE_ID = uuid4()

LEGAL_EVIDENCE = [{
    "source_id": "consumer-rights-guide", "title": "Guide", "page_number": 22,
    "chunk_index": 0, "text": "Warranty rules apply to vehicles.",
}]


def test_extract_citations_keeps_only_retrieved_evidence():
    text = (
        "See consumer-rights-guide:p22 for warranty rules, "
        "but invented-source:p9 and consumer-rights-guide:p99 are not evidence."
    )

    citations = services.extract_citations(text, LEGAL_EVIDENCE, [])

    assert citations == [{
        "source_id": "consumer-rights-guide",
        "location": "page 22",
        "quote": "Warranty rules apply to vehicles.",
    }]


def test_prepare_chat_stream_persists_user_message(monkeypatch):
    case = {"id": CASE_ID, "case_type": "contract", "description": "Unpaid contract.", "current_stage": "evidence", "lawyer_proposed_action": None}
    monkeypatch.setattr(services.repositories, "get_case", lambda _: case)
    monkeypatch.setattr(services.repositories, "list_case_messages", lambda *_: [])
    created = {}
    monkeypatch.setattr(
        services.repositories, "create_case_message",
        lambda payload: created.update(payload) or {"id": uuid4(), **payload},
    )
    monkeypatch.setattr(services, "embed_text", lambda _: [0.1, 0.2])
    monkeypatch.setattr(services.repositories, "search_legal_source_chunks", lambda *_: LEGAL_EVIDENCE)
    monkeypatch.setattr(services.repositories, "search_case_document_chunks", lambda *_: [])

    prepared = services.prepare_chat_stream(CASE_ID, "What happens next?")

    assert created["role"] == "user"
    assert created["content"] == "What happens next?"
    assert "What happens next?" in prepared["prompt"]
    assert prepared["legal_chunks"] == LEGAL_EVIDENCE


def test_prepare_chat_stream_rejects_blank_message(monkeypatch):
    monkeypatch.setattr(services.repositories, "get_case", lambda _: {"id": CASE_ID})
    monkeypatch.setattr(services, "embed_text", lambda _: pytest.fail("embedding should not run"))

    with pytest.raises(services.UploadError):
        services.prepare_chat_stream(CASE_ID, "   ")


@pytest.fixture
def client(monkeypatch):
    monkeypatch.setattr("app.main.initialize_database", lambda: None)
    with TestClient(app) as test_client:
        yield test_client


def _mock_stream_api(monkeypatch, events=None):
    monkeypatch.setattr(
        services, "prepare_chat_stream",
        lambda *_: {"user_message": {"id": str(uuid4()), "role": "user", "content": "Hi"}},
    )
    canned = events if events is not None else [
        {"type": "delta", "text": "Hello "},
        {"type": "delta", "text": "there."},
        {"type": "done", "message": {"id": str(uuid4()), "role": "assistant", "content": "Hello there."}},
    ]
    monkeypatch.setattr(services, "stream_chat_reply", lambda _: iter(canned))


def _parse_sse(body: str):
    events = []
    for part in body.split("\n\n"):
        for line in part.splitlines():
            if line.startswith("data:"):
                events.append(json.loads(line[5:].strip()))
    return events


def test_chat_stream_emits_sse_events(client, monkeypatch):
    _mock_stream_api(monkeypatch)

    response = client.post(f"/api/cases/{CASE_ID}/chat/stream", json={"message": "Hi"})

    assert response.status_code == 200
    assert "text/event-stream" in response.headers["content-type"]
    events = _parse_sse(response.text)
    assert [event["type"] for event in events] == ["user", "delta", "delta", "done"]
    assert "".join(event["text"] for event in events if event["type"] == "delta") == "Hello there."


def test_chat_stream_rejects_blank_and_missing_case(client, monkeypatch):
    def fail_prepare(case_id, message):
        if not message.strip():
            raise services.UploadError("Chat message is required.")
        raise services.UploadError("Case not found.", 404)

    monkeypatch.setattr(services, "prepare_chat_stream", fail_prepare)

    assert client.post(f"/api/cases/{CASE_ID}/chat/stream", json={"message": ""}).status_code == 422
    assert client.post(f"/api/cases/{CASE_ID}/chat/stream", json={"message": "   "}).status_code == 400
    assert client.post(f"/api/cases/{CASE_ID}/chat/stream", json={"message": "Hi"}).status_code == 404


def test_stream_chat_reply_stores_validated_citations(monkeypatch):
    prepared = {
        "case_id": CASE_ID, "case": {"id": CASE_ID}, "history": [], "message": "Hi",
        "prompt": "prompt", "legal_chunks": LEGAL_EVIDENCE, "document_chunks": [],
        "user_message": {"id": str(uuid4())},
    }
    monkeypatch.setattr(
        services.ai_provider, "PROVIDER", "ollama",
    )
    monkeypatch.setattr(
        services.ai_provider, "stream_ollama_tokens",
        lambda _: iter(["See consumer-rights-guide:p22 and invented-source:p9."]),
    )
    stored = {}
    monkeypatch.setattr(
        services.repositories, "create_case_message",
        lambda payload: stored.update(payload) or {"id": uuid4(), "created_at": datetime.now(timezone.utc), **payload},
    )

    events = list(services.stream_chat_reply(prepared))

    assert events[0] == {"type": "delta", "text": "See consumer-rights-guide:p22 and invented-source:p9."}
    assert events[1]["type"] == "done"
    assert stored["citations"] == [{
        "source_id": "consumer-rights-guide",
        "location": "page 22",
        "quote": "Warranty rules apply to vehicles.",
    }]
