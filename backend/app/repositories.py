import json
from datetime import datetime
from uuid import UUID, uuid4

from app.database import get_connection
from app.schemas import CaseCreate


CASE_COLUMNS = "id, case_type, description, current_stage, status, lawyer_proposed_action, created_at"
DOCUMENT_COLUMNS = "id, case_id, original_filename, mime_type, size_bytes, sha256, storage_path, processing_status, error, created_at"
PAGE_COLUMNS = "id, document_id, page_number, text, language, extraction_method, quality"
CHUNK_COLUMNS = "id, document_id, page_number, chunk_index, text, embedding"
LEGAL_SOURCE_COLUMNS = "source_id, title, source_url, publisher, source_type, jurisdiction, language, case_categories, sha256, size_bytes, retrieved_at"


def create_case(case: CaseCreate) -> dict[str, object]:
    case_id = uuid4()
    with get_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                f"""
                INSERT INTO cases (id, case_type, description, current_stage, lawyer_proposed_action)
                VALUES (%s, %s, %s, %s, %s)
                RETURNING {CASE_COLUMNS}
                """,
                (
                    case_id,
                    case.case_type,
                    case.description,
                    case.current_stage,
                    case.lawyer_proposed_action,
                ),
            )
            row = cursor.fetchone()
        connection.commit()
    return _row_to_dict(row, CASE_COLUMNS)


def get_case(case_id: UUID) -> dict[str, object] | None:
    with get_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                f"SELECT {CASE_COLUMNS} FROM cases WHERE id = %s",
                (case_id,),
            )
            row = cursor.fetchone()
    return _row_to_dict(row, CASE_COLUMNS) if row else None


def list_cases() -> list[dict[str, object]]:
    with get_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                f"SELECT {CASE_COLUMNS} FROM cases ORDER BY created_at DESC"
            )
            rows = cursor.fetchall()
    return [_row_to_dict(row, CASE_COLUMNS) for row in rows]


def case_exists(case_id: UUID) -> bool:
    with get_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1 FROM cases WHERE id = %s", (case_id,))
            return cursor.fetchone() is not None


def create_document(document: dict[str, object]) -> dict[str, object]:
    with get_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                f"""
                INSERT INTO documents (
                    id, case_id, original_filename, mime_type, size_bytes,
                    sha256, storage_path
                ) VALUES (%s, %s, %s, %s, %s, %s, %s)
                RETURNING {DOCUMENT_COLUMNS}
                """,
                (
                    document["id"], document["case_id"], document["original_filename"],
                    document["mime_type"], document["size_bytes"], document["sha256"],
                    document["storage_path"],
                ),
            )
            row = cursor.fetchone()
        connection.commit()
    return _row_to_dict(row, DOCUMENT_COLUMNS)


def get_document(document_id: UUID) -> dict[str, object] | None:
    with get_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                f"SELECT {DOCUMENT_COLUMNS} FROM documents WHERE id = %s",
                (document_id,),
            )
            row = cursor.fetchone()
    return _row_to_dict(row, DOCUMENT_COLUMNS) if row else None


def get_document_pages(document_id: UUID) -> list[dict[str, object]]:
    with get_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                f"SELECT {PAGE_COLUMNS} FROM document_pages WHERE document_id = %s ORDER BY page_number",
                (document_id,),
            )
            rows = cursor.fetchall()
    return [_row_to_dict(row, PAGE_COLUMNS) for row in rows]


def update_document_processing(document_id: UUID, processing_status: str, error: str | None = None) -> None:
    with get_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                "UPDATE documents SET processing_status = %s, error = %s WHERE id = %s",
                (processing_status, error, document_id),
            )
        connection.commit()


def replace_document_pages(document_id: UUID, pages: list[dict[str, object]]) -> None:
    with get_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute("DELETE FROM document_pages WHERE document_id = %s", (document_id,))
            for page in pages:
                cursor.execute(
                    f"""
                    INSERT INTO document_pages ({PAGE_COLUMNS})
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                    """,
                    (
                        uuid4(), document_id, page["page_number"], page["text"],
                        page["language"], page["extraction_method"], page["quality"],
                    ),
                )
        connection.commit()


def replace_document_chunks(document_id: UUID, chunks: list[dict[str, object]]) -> None:
    with get_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute("DELETE FROM document_chunks WHERE document_id = %s", (document_id,))
            for chunk in chunks:
                cursor.execute(
                    f"""
                    INSERT INTO document_chunks ({CHUNK_COLUMNS})
                    VALUES (%s, %s, %s, %s, %s, %s::vector)
                    """,
                    (
                        uuid4(), document_id, chunk["page_number"], chunk["chunk_index"],
                        chunk["text"], _vector_literal(chunk["embedding"]),
                    ),
                )
        connection.commit()


def search_document_chunks(embedding: list[float], limit: int = 5) -> list[dict[str, object]]:
    vector = _vector_literal(embedding)
    with get_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT id, document_id, page_number, chunk_index, text,
                       embedding <=> %s::vector AS distance
                FROM document_chunks
                WHERE embedding IS NOT NULL
                ORDER BY embedding <=> %s::vector
                LIMIT %s
                """,
                (vector, vector, limit),
            )
            rows = cursor.fetchall()
    return [
        dict(zip(("id", "document_id", "page_number", "chunk_index", "text", "distance"), row, strict=True))
        for row in rows
    ]


def get_legal_source_sha256(source_id: str) -> str | None:
    with get_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute("SELECT sha256 FROM legal_sources WHERE source_id = %s", (source_id,))
            row = cursor.fetchone()
    return row[0] if row else None


def replace_legal_source(source: dict[str, object], pages: list[dict[str, object]], chunks: list[dict[str, object]]) -> None:
    """Replace one source and all derived records in one database transaction."""
    with get_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO legal_sources (
                    source_id, title, source_url, publisher, source_type, jurisdiction,
                    language, case_categories, sha256, size_bytes, retrieved_at, updated_at
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s::jsonb, %s, %s, %s, NOW())
                ON CONFLICT (source_id) DO UPDATE SET
                    title = EXCLUDED.title, source_url = EXCLUDED.source_url,
                    publisher = EXCLUDED.publisher, source_type = EXCLUDED.source_type,
                    jurisdiction = EXCLUDED.jurisdiction, language = EXCLUDED.language,
                    case_categories = EXCLUDED.case_categories, sha256 = EXCLUDED.sha256,
                    size_bytes = EXCLUDED.size_bytes, retrieved_at = EXCLUDED.retrieved_at,
                    updated_at = NOW()
                """,
                (
                    source["source_id"], source["title"], source["url"], source["publisher"],
                    source["source_type"], source["jurisdiction"], source["language"],
                    json.dumps(source["case_categories"]), source["sha256"], source["size_bytes"],
                    source.get("retrieved_at"),
                ),
            )
            cursor.execute("DELETE FROM legal_source_chunks WHERE source_id = %s", (source["source_id"],))
            cursor.execute("DELETE FROM legal_source_pages WHERE source_id = %s", (source["source_id"],))
            for page in pages:
                cursor.execute(
                    """INSERT INTO legal_source_pages
                       (id, source_id, page_number, text, language, extraction_method, quality)
                       VALUES (%s, %s, %s, %s, %s, %s, %s)""",
                    (uuid4(), source["source_id"], page["page_number"], page["text"], page["language"], page["extraction_method"], page["quality"]),
                )
            for chunk in chunks:
                cursor.execute(
                    """INSERT INTO legal_source_chunks
                       (id, source_id, page_number, chunk_index, text, embedding)
                       VALUES (%s, %s, %s, %s, %s, %s::vector)""",
                    (uuid4(), source["source_id"], chunk["page_number"], chunk["chunk_index"], chunk["text"], _vector_literal(chunk["embedding"])),
                )
        connection.commit()


def search_legal_source_chunks(embedding: list[float], jurisdiction: str, case_category: str | None, limit: int) -> list[dict[str, object]]:
    vector = _vector_literal(embedding)
    category_filter = ""
    parameters: list[object] = [vector, jurisdiction]
    if case_category:
        category_filter = " AND ls.case_categories @> %s::jsonb"
        parameters.append(json.dumps([case_category]))
    parameters.extend([vector, limit])
    with get_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                f"""
                SELECT lsc.source_id, ls.title, ls.source_url, ls.publisher, ls.source_type,
                       ls.jurisdiction, ls.language, lsc.page_number, lsc.chunk_index, lsc.text,
                       lsc.embedding <=> %s::vector AS distance
                FROM legal_source_chunks lsc
                JOIN legal_sources ls ON ls.source_id = lsc.source_id
                WHERE ls.jurisdiction = %s {category_filter}
                ORDER BY lsc.embedding <=> %s::vector
                LIMIT %s
                """,
                parameters,
            )
            rows = cursor.fetchall()
    columns = ("source_id", "title", "source_url", "publisher", "source_type", "jurisdiction", "language", "page_number", "chunk_index", "text", "distance")
    return [dict(zip(columns, row, strict=True)) for row in rows]


ASSESSMENT_COLUMNS = "id, case_id, summary, what_happens_next, risks, recommended_lawyer_questions, citations, provider, model, requires_human_review, created_at"
MESSAGE_COLUMNS = "id, case_id, role, content, citations, requires_human_review, created_at"


def search_case_document_chunks(embedding: list[float], case_id: UUID, limit: int = 5) -> list[dict[str, object]]:
    vector = _vector_literal(embedding)
    with get_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT dc.id, dc.document_id, dc.page_number, dc.chunk_index, dc.text,
                       dc.embedding <=> %s::vector AS distance
                FROM document_chunks dc
                JOIN documents d ON d.id = dc.document_id
                WHERE dc.embedding IS NOT NULL AND d.case_id = %s
                ORDER BY dc.embedding <=> %s::vector
                LIMIT %s
                """,
                (vector, case_id, vector, limit),
            )
            rows = cursor.fetchall()
    return [
        dict(zip(("id", "document_id", "page_number", "chunk_index", "text", "distance"), row, strict=True))
        for row in rows
    ]


def create_assessment(assessment: dict[str, object]) -> dict[str, object]:
    assessment_id = uuid4()
    with get_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                f"""
                INSERT INTO assessments (
                    id, case_id, summary, what_happens_next, risks,
                    recommended_lawyer_questions, citations, provider, model
                ) VALUES (%s, %s, %s, %s::jsonb, %s::jsonb, %s::jsonb, %s::jsonb, %s, %s)
                RETURNING {ASSESSMENT_COLUMNS}
                """,
                (
                    assessment_id,
                    assessment["case_id"],
                    assessment["summary"],
                    json.dumps(assessment["what_happens_next"]),
                    json.dumps(assessment["risks"]),
                    json.dumps(assessment["recommended_lawyer_questions"]),
                    json.dumps(assessment["citations"]),
                    assessment.get("provider", "ollama"),
                    assessment.get("model", ""),
                ),
            )
            row = cursor.fetchone()
        connection.commit()
    return _row_to_dict(row, ASSESSMENT_COLUMNS)


def list_assessments(case_id: UUID) -> list[dict[str, object]]:
    with get_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                f"SELECT {ASSESSMENT_COLUMNS} FROM assessments WHERE case_id = %s ORDER BY created_at DESC",
                (case_id,),
            )
            rows = cursor.fetchall()
    return [_row_to_dict(row, ASSESSMENT_COLUMNS) for row in rows]


def create_case_message(message: dict[str, object]) -> dict[str, object]:
    message_id = uuid4()
    with get_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                f"""
                INSERT INTO case_messages (id, case_id, role, content, citations)
                VALUES (%s, %s, %s, %s, %s::jsonb)
                RETURNING {MESSAGE_COLUMNS}
                """,
                (
                    message_id,
                    message["case_id"],
                    message["role"],
                    message["content"],
                    json.dumps(message.get("citations", [])),
                ),
            )
            row = cursor.fetchone()
        connection.commit()
    return _row_to_dict(row, MESSAGE_COLUMNS)


def list_case_messages(case_id: UUID, limit: int = 50) -> list[dict[str, object]]:
    with get_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                f"""
                SELECT {MESSAGE_COLUMNS} FROM case_messages
                WHERE case_id = %s ORDER BY created_at ASC LIMIT %s
                """,
                (case_id, limit),
            )
            rows = cursor.fetchall()
    return [_row_to_dict(row, MESSAGE_COLUMNS) for row in rows]


def _vector_literal(values: object) -> str:
    return "[" + ",".join(str(float(value)) for value in values) + "]"


def _row_to_dict(row: tuple[object, ...], columns: str) -> dict[str, object]:
    return dict(
        zip(
            columns.split(", "),
            row,
            strict=True,
        )
    )
