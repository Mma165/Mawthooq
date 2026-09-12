from app import database
from app import rag


def test_create_indexes_covers_join_and_listing_columns():
    expected = [
        "documents_case_id_idx",
        "document_pages_document_id_idx",
        "document_chunks_document_id_idx",
        "legal_source_chunks_source_id_idx",
        "legal_source_pages_source_id_idx",
        "assessments_case_id_idx",
        "case_messages_case_id_idx",
        "cases_created_at_idx",
    ]
    for index_name in expected:
        assert index_name in database.CREATE_INDEXES


def test_embed_text_caches_identical_queries(monkeypatch):
    rag.embed_text.cache_clear()
    calls = []

    class FakeResponse:
        def raise_for_status(self):
            return None

        def json(self):
            return {"embedding": [0.1, 0.2]}

    def fake_post(*_, **__):
        calls.append(1)
        return FakeResponse()

    monkeypatch.setattr(rag.httpx, "post", fake_post)
    try:
        assert rag.embed_text("warranty rights") == [0.1, 0.2]
        assert rag.embed_text("warranty rights") == [0.1, 0.2]
        assert len(calls) == 1
    finally:
        rag.embed_text.cache_clear()


def test_pool_is_lazy_singleton(monkeypatch):
    import psycopg_pool

    created = []

    class FakePool:
        def __init__(self, *args, **kwargs):
            created.append((args, kwargs))

    monkeypatch.setattr(psycopg_pool, "ConnectionPool", FakePool)
    monkeypatch.setattr(database, "_pool", None)
    try:
        assert database._get_pool() is database._get_pool()
        assert len(created) == 1
    finally:
        database._pool = None
