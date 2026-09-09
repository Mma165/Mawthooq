from datetime import datetime
from uuid import UUID, uuid4

from app.database import get_connection
from app.schemas import CaseCreate


CASE_COLUMNS = "id, case_type, description, current_stage, status, lawyer_proposed_action, created_at"


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
    return _row_to_dict(row)


def get_case(case_id: UUID) -> dict[str, object] | None:
    with get_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                f"SELECT {CASE_COLUMNS} FROM cases WHERE id = %s",
                (case_id,),
            )
            row = cursor.fetchone()
    return _row_to_dict(row) if row else None


def list_cases() -> list[dict[str, object]]:
    with get_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                f"SELECT {CASE_COLUMNS} FROM cases ORDER BY created_at DESC"
            )
            rows = cursor.fetchall()
    return [_row_to_dict(row) for row in rows]


def _row_to_dict(row: tuple[object, ...]) -> dict[str, object]:
    return dict(
        zip(
            CASE_COLUMNS.split(", "),
            row,
            strict=True,
        )
    )
