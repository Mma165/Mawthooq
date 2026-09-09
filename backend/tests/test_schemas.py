import pytest
from pydantic import ValidationError

from app.schemas import CaseCreate


def test_valid_case_payload_is_accepted() -> None:
    case = CaseCreate(
        case_type="commercial_dispute",
        description="Dispute concerning an unpaid supply contract.",
        current_stage="evidence",
    )
    assert case.case_type == "commercial_dispute"


def test_short_description_is_rejected() -> None:
    with pytest.raises(ValidationError):
        CaseCreate(
            case_type="commercial_dispute",
            description="Too short",
            current_stage="evidence",
        )


def test_unknown_fields_are_rejected() -> None:
    with pytest.raises(ValidationError):
        CaseCreate(
            case_type="commercial_dispute",
            description="A valid case description.",
            current_stage="evidence",
            unexpected="value",
        )
