import json

import psycopg
import pytest
from fastapi.testclient import TestClient

from app import services
from app.main import app


@pytest.fixture
def client(monkeypatch):
    monkeypatch.setattr("app.main.initialize_database", lambda: None)
    with TestClient(app) as test_client:
        yield test_client


_DEFAULT_RESULT = [{
    "source_id": "consumer-rights-guide",
    "title": "Consumer rights guide",
    "source_url": "https://example.test/guide.pdf",
    "publisher": "Ministry of Commerce",
    "source_type": "guidance",
    "jurisdiction": "Saudi Arabia",
    "language": "ar",
    "page_number": 3,
    "chunk_index": 0,
    "text": "Consumer warranty applies.",
    "distance": 0.37,
}]


def _match(monkeypatch, results=None):
    monkeypatch.setattr(services, "embed_text", lambda _: [0.1, 0.2])
    monkeypatch.setattr(
        services.repositories,
        "search_legal_source_chunks",
        lambda *_: results if results is not None else _DEFAULT_RESULT,
    )


def test_legal_source_search_returns_filtered_results(client, monkeypatch):
    _match(monkeypatch)

    response = client.get(
        "/api/legal-sources/search?query=warranty&jurisdiction=Saudi%20Arabia&case_category=contract"
    )

    assert response.status_code == 200
    body = response.json()
    assert body["jurisdiction"] == "Saudi Arabia"
    assert body["case_category"] == "contract"
    result = body["results"][0]
    assert result["source_id"] == "consumer-rights-guide"
    assert result["title"] == "Consumer rights guide"
    assert result["publisher"] == "Ministry of Commerce"
    assert result["source_type"] == "guidance"
    assert result["page_number"] == 3
    assert result["citation"] == "consumer-rights-guide:p3"
    assert result["distance"] == 0.37


def test_legal_source_search_returns_empty_results(client, monkeypatch):
    _match(monkeypatch, results=[])

    response = client.get(
        "/api/legal-sources/search?query=unmatched&jurisdiction=Saudi%20Arabia"
    )

    assert response.status_code == 200
    assert response.json()["results"] == []


def test_legal_source_search_rejects_blank_query_without_embedding(client, monkeypatch):
    monkeypatch.setattr(services, "embed_text", lambda _: pytest.fail("embedding should not run"))

    response = client.get(
        "/api/legal-sources/search?query=%20%20&jurisdiction=Saudi%20Arabia"
    )

    assert response.status_code == 400
    assert "query" in response.json()["detail"].lower()


def test_legal_source_search_rejects_missing_jurisdiction(client, monkeypatch):
    monkeypatch.setattr(services, "embed_text", lambda _: pytest.fail("embedding should not run"))

    response = client.get("/api/legal-sources/search?query=contract")

    assert response.status_code == 422
    body = response.json()
    errors = body.get("detail", [])
    assert any("jurisdiction" in (e.get("loc") or [None, ""])[1] for e in errors)


def test_legal_source_search_rejects_invalid_category_without_embedding(client, monkeypatch):
    monkeypatch.setattr(services, "embed_text", lambda _: pytest.fail("embedding should not run"))

    response = client.get(
        "/api/legal-sources/search?query=contract&jurisdiction=Saudi%20Arabia&case_category=invalid"
    )

    assert response.status_code == 422


@pytest.mark.parametrize("limit", ["0", "21", "abc"])
def test_legal_source_search_rejects_invalid_limit(client, monkeypatch, limit):
    monkeypatch.setattr(services, "embed_text", lambda _: pytest.fail("embedding should not run"))

    response = client.get(
        f"/api/legal-sources/search?query=contract&jurisdiction=Saudi%20Arabia&limit={limit}"
    )

    assert response.status_code == 422
    assert "limit" in json.dumps(response.json()).lower()


def test_legal_source_search_returns_503_on_embedding_failure(client, monkeypatch):
    def fail_embed(_):
        raise ValueError("Embedding provider returned no embedding")

    monkeypatch.setattr(services, "embed_text", fail_embed)

    response = client.get(
        "/api/legal-sources/search?query=contract&jurisdiction=Saudi%20Arabia"
    )

    assert response.status_code == 503
    assert "unavailable" in response.json()["detail"].lower()


def test_legal_source_search_returns_503_on_storage_failure(client, monkeypatch):
    monkeypatch.setattr(services, "embed_text", lambda _: [0.1, 0.2])
    monkeypatch.setattr(
        services.repositories,
        "search_legal_source_chunks",
        lambda *_: (_ for _ in ()).throw(psycopg.OperationalError("database down")),
    )

    response = client.get(
        "/api/legal-sources/search?query=contract&jurisdiction=Saudi%20Arabia"
    )

    assert response.status_code == 503


def test_search_documents_blank_query_returns_client_error_without_ollama(client, monkeypatch):
    monkeypatch.setattr(services, "embed_text", lambda _: pytest.fail("embedding should not run"))

    response = client.get("/api/search?query=%20%20")

    assert response.status_code == 400
    assert "query" in response.json()["detail"].lower()


def test_search_documents_rejects_invalid_limit(client, monkeypatch):
    monkeypatch.setattr(services, "embed_text", lambda _: pytest.fail("embedding should not run"))

    response = client.get("/api/search?query=contract&limit=21")

    assert response.status_code == 422