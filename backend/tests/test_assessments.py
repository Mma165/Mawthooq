from datetime import datetime, timezone
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from app import services
from app.main import app


CASE_ID = uuid4()


def _case():
    return {
        "id": CASE_ID,
        "case_type": "commercial_dispute",
        "description": "Dispute concerning an unpaid supply contract.",
        "current_stage": "evidence",
        "status": "active",
        "lawyer_proposed_action": "Submit supporting payment records",
        "created_at": datetime.now(timezone.utc),
    }


def _generated_assessment():
    return {
        "summary": "The supply contract is unpaid.",
        "what_happens_next": [{"text": "File a claim", "citations": ["consumer-rights-guide:p10"]}],
        "risks": ["Missing payment records"],
        "recommended_lawyer_questions": ["Is the contract signed?"],
        "citations": [{"source_id": "consumer-rights-guide", "location": "page 10", "quote": "..."}],
        "provider": "ollama",
        "model": "llama3.2:3b",
        "requires_human_review": True,
    }


def _stored_assessment():
    return {
        **_generated_assessment(),
        "id": uuid4(),
        "case_id": CASE_ID,
        "created_at": datetime.now(timezone.utc),
    }


def _mock_retrieval(monkeypatch, legal=None, documents=None):
    monkeypatch.setattr(services, "embed_text", lambda _: [0.1, 0.2])
    monkeypatch.setattr(
        services.repositories, "search_legal_source_chunks", lambda *_: legal or []
    )
    monkeypatch.setattr(
        services.repositories, "search_case_document_chunks", lambda *_: documents or []
    )


def test_generate_assessment_persists_grounded_result(monkeypatch):
    monkeypatch.setattr(services.repositories, "get_case", lambda _: _case())
    _mock_retrieval(monkeypatch)
    monkeypatch.setattr(
        services.ai_provider, "generate_case_assessment", lambda *_: _generated_assessment()
    )
    stored = {}
    monkeypatch.setattr(
        services.repositories, "create_assessment", lambda payload: stored.update(payload) or _stored_assessment()
    )

    services.generate_assessment(CASE_ID)

    assert stored["case_id"] == CASE_ID
    assert stored["summary"] == "The supply contract is unpaid."
    assert stored["provider"] == "ollama"


def test_generate_assessment_rejects_missing_case(monkeypatch):
    monkeypatch.setattr(services.repositories, "get_case", lambda _: None)

    with pytest.raises(services.UploadError) as error:
        services.generate_assessment(CASE_ID)

    assert error.value.status_code == 404


def test_generate_assessment_returns_503_when_provider_fails(monkeypatch):
    monkeypatch.setattr(services.repositories, "get_case", lambda _: _case())
    _mock_retrieval(monkeypatch)

    def fail_generation(*_):
        raise RuntimeError("Ollama generation failed")

    monkeypatch.setattr(services.ai_provider, "generate_case_assessment", fail_generation)

    with pytest.raises(services.UploadError) as error:
        services.generate_assessment(CASE_ID)

    assert error.value.status_code == 503


def test_chat_with_case_stores_both_messages(monkeypatch):
    monkeypatch.setattr(services.repositories, "get_case", lambda _: _case())
    monkeypatch.setattr(services.repositories, "list_case_messages", lambda *_: [])
    _mock_retrieval(monkeypatch)
    monkeypatch.setattr(
        services.ai_provider,
        "generate_case_chat_reply",
        lambda *_: {"reply": "Verify with your lawyer.", "citations": [], "provider": "ollama", "model": "m", "requires_human_review": True},
    )
    created = []

    def fake_create(payload):
        record = {"id": uuid4(), "created_at": datetime.now(timezone.utc), "requires_human_review": True, **payload}
        created.append(record)
        return record

    monkeypatch.setattr(services.repositories, "create_case_message", fake_create)

    result = services.chat_with_case(CASE_ID, "What happens next?")

    assert [message["role"] for message in created] == ["user", "assistant"]
    assert result["assistant_message"]["content"] == "Verify with your lawyer."


def test_chat_with_case_rejects_blank_message(monkeypatch):
    monkeypatch.setattr(services.repositories, "get_case", lambda _: _case())
    monkeypatch.setattr(services, "embed_text", lambda _: pytest.fail("embedding should not run"))

    with pytest.raises(services.UploadError):
        services.chat_with_case(CASE_ID, "   ")


@pytest.fixture
def client(monkeypatch):
    monkeypatch.setattr("app.main.initialize_database", lambda: None)
    with TestClient(app) as test_client:
        yield test_client


def _mock_assessment_api(monkeypatch):
    monkeypatch.setattr(services.repositories, "get_case", lambda _: _case())
    monkeypatch.setattr(services.repositories, "case_exists", lambda _: True)
    _mock_retrieval(monkeypatch)
    monkeypatch.setattr(
        services.ai_provider, "generate_case_assessment", lambda *_: _generated_assessment()
    )
    monkeypatch.setattr(services.repositories, "create_assessment", lambda payload: _stored_assessment())
    monkeypatch.setattr(services.repositories, "list_assessments", lambda *_: [_stored_assessment()])
    monkeypatch.setattr(services.repositories, "list_case_messages", lambda *_: [])
    monkeypatch.setattr(
        services.ai_provider,
        "generate_case_chat_reply",
        lambda *_: {"reply": "Verify with your lawyer.", "citations": [], "provider": "ollama", "model": "m", "requires_human_review": True},
    )

    def fake_create(payload):
        return {"id": uuid4(), "created_at": datetime.now(timezone.utc), "requires_human_review": True, **payload}

    monkeypatch.setattr(services.repositories, "create_case_message", fake_create)


def test_assessment_api_creates_and_lists(client, monkeypatch):
    _mock_assessment_api(monkeypatch)

    created = client.post(f"/api/cases/{CASE_ID}/assessments")
    assert created.status_code == 201
    assert created.json()["requires_human_review"] is True

    listed = client.get(f"/api/cases/{CASE_ID}/assessments")
    assert listed.status_code == 200
    assert len(listed.json()) == 1


def test_assessment_api_returns_404_for_missing_case(client, monkeypatch):
    monkeypatch.setattr(services.repositories, "get_case", lambda _: None)
    monkeypatch.setattr(services.repositories, "case_exists", lambda _: False)

    assert client.post(f"/api/cases/{CASE_ID}/assessments").status_code == 404
    assert client.get(f"/api/cases/{CASE_ID}/assessments").status_code == 404


def test_chat_api_round_trip(client, monkeypatch):
    _mock_assessment_api(monkeypatch)

    response = client.post(f"/api/cases/{CASE_ID}/chat", json={"message": "What happens next?"})
    assert response.status_code == 200
    body = response.json()
    assert body["user_message"]["role"] == "user"
    assert body["assistant_message"]["role"] == "assistant"

    assert client.post(f"/api/cases/{CASE_ID}/chat", json={"message": ""}).status_code == 422
    assert client.post(f"/api/cases/{CASE_ID}/chat", json={"message": "   "}).status_code == 400
