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


def get_connection() -> psycopg.Connection:
    return psycopg.connect(DATABASE_URL)


def initialize_database() -> None:
    with get_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute("CREATE EXTENSION IF NOT EXISTS vector")
            cursor.execute(CREATE_CASES_TABLE)
        connection.commit()
