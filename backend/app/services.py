from uuid import UUID

from app import repositories
from app.schemas import CaseCreate


def create_case(case: CaseCreate) -> dict[str, object]:
    return repositories.create_case(case)


def get_case(case_id: UUID) -> dict[str, object] | None:
    return repositories.get_case(case_id)
