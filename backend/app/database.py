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


def get_connection() -> psycopg.Connection:
    return psycopg.connect(DATABASE_URL)


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
        connection.commit()
