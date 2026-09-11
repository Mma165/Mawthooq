import pytest

from app import services


def test_legal_search_returns_source_citation(monkeypatch):
    monkeypatch.setattr(services, "embed_text", lambda _: [0.1, 0.2])
    monkeypatch.setattr(services.repositories, "search_legal_source_chunks", lambda *_: [{
        "source_id": "official-source", "title": "Official source", "source_url": "https://example.test",
        "publisher": "Authority", "source_type": "binding_law", "jurisdiction": "Saudi Arabia",
        "language": "ar", "page_number": 4, "chunk_index": 0, "text": "Relevant passage", "distance": 0.12,
    }])

    results = services.search_legal_sources("contract evidence", "Saudi Arabia", "contract")

    assert results[0]["citation"] == "official-source:p4"


def test_legal_search_rejects_blank_query_without_embedding(monkeypatch):
    monkeypatch.setattr(services, "embed_text", lambda _: pytest.fail("embedding should not run"))

    with pytest.raises(services.UploadError, match="query"):
        services.search_legal_sources("   ", "Saudi Arabia", None)


def test_legal_search_rejects_invalid_category_without_embedding(monkeypatch):
    monkeypatch.setattr(services, "embed_text", lambda _: pytest.fail("embedding should not run"))

    with pytest.raises(services.UploadError) as error:
        services.search_legal_sources("contract", "Saudi Arabia", "invalid")

    assert error.value.status_code == 422
