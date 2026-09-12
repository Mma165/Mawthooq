import psycopg

from app.config import DATABASE_URL


CREATE_CASES_TABLE = """
CREATE TABLE IF NOT EXISTS cases (
    id UUID PRIMARY KEY,
    case_type VARCHAR(64) NOT NULL,
    description TEXT NOT NULL,
    current_stage VARCHAR(64) NOT NULL,
    status VARCHAR(16) NOT NULL DEFAULT 'active',
    lawyer_proposed_action TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
)
"""

CREATE_DOCUMENTS_TABLE = """
CREATE TABLE IF NOT EXISTS documents (
    id UUID PRIMARY KEY,
    case_id UUID NOT NULL REFERENCES cases(id) ON DELETE CASCADE,
    original_filename VARCHAR(255) NOT NULL,
    mime_type VARCHAR(127) NOT NULL,
    size_bytes BIGINT NOT NULL,
    sha256 CHAR(64) NOT NULL,
    storage_path TEXT NOT NULL,
    processing_status VARCHAR(32) NOT NULL DEFAULT 'uploaded',
    error TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
)
"""

CREATE_DOCUMENT_PAGES_TABLE = """
CREATE TABLE IF NOT EXISTS document_pages (
    id UUID PRIMARY KEY,
    document_id UUID NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
    page_number INTEGER NOT NULL,
    text TEXT NOT NULL,
    language VARCHAR(16) NOT NULL,
    extraction_method VARCHAR(32) NOT NULL,
    quality VARCHAR(16) NOT NULL,
    UNIQUE (document_id, page_number)
)
"""

CREATE_DOCUMENT_CHUNKS_TABLE = """
CREATE TABLE IF NOT EXISTS document_chunks (
    id UUID PRIMARY KEY,
    document_id UUID NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
    page_number INTEGER NOT NULL,
    chunk_index INTEGER NOT NULL,
    text TEXT NOT NULL,
    embedding vector,
    UNIQUE (document_id, page_number, chunk_index)
)
"""

CREATE_LEGAL_SOURCES_TABLE = """
CREATE TABLE IF NOT EXISTS legal_sources (
    source_id VARCHAR(128) PRIMARY KEY,
    title TEXT NOT NULL,
    source_url TEXT NOT NULL,
    publisher TEXT NOT NULL,
    source_type VARCHAR(64) NOT NULL,
    jurisdiction VARCHAR(128) NOT NULL,
    language VARCHAR(16) NOT NULL,
    case_categories JSONB NOT NULL,
    sha256 CHAR(64) NOT NULL,
    size_bytes BIGINT NOT NULL,
    retrieved_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
)
"""

CREATE_LEGAL_SOURCE_PAGES_TABLE = """
CREATE TABLE IF NOT EXISTS legal_source_pages (
    id UUID PRIMARY KEY,
    source_id VARCHAR(128) NOT NULL REFERENCES legal_sources(source_id) ON DELETE CASCADE,
    page_number INTEGER NOT NULL,
    text TEXT NOT NULL,
    language VARCHAR(16) NOT NULL,
    extraction_method VARCHAR(32) NOT NULL,
    quality VARCHAR(16) NOT NULL,
    UNIQUE (source_id, page_number)
)
"""

CREATE_LEGAL_SOURCE_CHUNKS_TABLE = """
CREATE TABLE IF NOT EXISTS legal_source_chunks (
    id UUID PRIMARY KEY,
    source_id VARCHAR(128) NOT NULL REFERENCES legal_sources(source_id) ON DELETE CASCADE,
    page_number INTEGER NOT NULL,
    chunk_index INTEGER NOT NULL,
    text TEXT NOT NULL,
    embedding vector NOT NULL,
    UNIQUE (source_id, page_number, chunk_index)
)
"""

CREATE_ASSESSMENTS_TABLE = """
CREATE TABLE IF NOT EXISTS assessments (
    id UUID PRIMARY KEY,
    case_id UUID NOT NULL REFERENCES cases(id) ON DELETE CASCADE,
    summary TEXT NOT NULL,
    what_happens_next JSONB NOT NULL,
    risks JSONB NOT NULL,
    recommended_lawyer_questions JSONB NOT NULL,
    citations JSONB NOT NULL,
    provider VARCHAR(32) NOT NULL DEFAULT 'ollama',
    model VARCHAR(128) NOT NULL DEFAULT '',
    requires_human_review BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
)
"""

CREATE_CASE_MESSAGES_TABLE = """
CREATE TABLE IF NOT EXISTS case_messages (
    id UUID PRIMARY KEY,
    case_id UUID NOT NULL REFERENCES cases(id) ON DELETE CASCADE,
    role VARCHAR(16) NOT NULL,
    content TEXT NOT NULL,
    citations JSONB NOT NULL DEFAULT '[]',
    requires_human_review BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
)
"""


# NOTE: no pgvector HNSW/IVFFlat index is created on the embedding columns.
# The vector columns are intentionally dimensionless so the embedding model can
# change without a schema migration, and pgvector refuses approximate indexes
# on dimensionless columns. At the current corpus size (hundreds of rows) a
# sequential scan is optimal; revisit only past ~10k chunks, and only after
# pinning the columns to vector(<dim>).
CREATE_INDEXES = """
CREATE INDEX IF NOT EXISTS documents_case_id_idx ON documents (case_id);
CREATE INDEX IF NOT EXISTS document_pages_document_id_idx ON document_pages (document_id);
CREATE INDEX IF NOT EXISTS document_chunks_document_id_idx ON document_chunks (document_id);
CREATE INDEX IF NOT EXISTS legal_source_chunks_source_id_idx ON legal_source_chunks (source_id);
CREATE INDEX IF NOT EXISTS legal_source_pages_source_id_idx ON legal_source_pages (source_id);
CREATE INDEX IF NOT EXISTS assessments_case_id_idx ON assessments (case_id);
CREATE INDEX IF NOT EXISTS case_messages_case_id_idx ON case_messages (case_id);
CREATE INDEX IF NOT EXISTS cases_created_at_idx ON cases (created_at DESC);
"""


_pool = None


def _get_pool():
    global _pool
    if _pool is None:
        from psycopg_pool import ConnectionPool

        _pool = ConnectionPool(DATABASE_URL, min_size=1, max_size=10, open=True)
    return _pool


def get_connection():
    """Yield a pooled connection; kept as a context manager for callers."""
    return _get_pool().connection()


def close_pool() -> None:
    global _pool
    if _pool is not None:
        _pool.close()
        _pool = None


def initialize_database() -> None:
    with get_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute("CREATE EXTENSION IF NOT EXISTS vector")
            cursor.execute(CREATE_CASES_TABLE)
            cursor.execute(CREATE_DOCUMENTS_TABLE)
            cursor.execute(CREATE_DOCUMENT_PAGES_TABLE)
            cursor.execute(CREATE_DOCUMENT_CHUNKS_TABLE)
            cursor.execute(CREATE_LEGAL_SOURCES_TABLE)
            cursor.execute(CREATE_LEGAL_SOURCE_PAGES_TABLE)
            cursor.execute(CREATE_LEGAL_SOURCE_CHUNKS_TABLE)
            cursor.execute(CREATE_ASSESSMENTS_TABLE)
            cursor.execute(CREATE_CASE_MESSAGES_TABLE)
            for statement in CREATE_INDEXES.strip().split(";"):
                if statement.strip():
                    cursor.execute(statement)
        connection.commit()
