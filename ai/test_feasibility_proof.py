import pytest

from ai.feasibility_proof import extract_hearing_update


@pytest.mark.parametrize(
    ("text", "status", "event_date", "requires_review"),
    [
        ("Hearing postponed to 15 October 2026.", "ready", "2026-10-15", False),
        ("HEARING POSTPONED TO 5 January 2027", "ready", "2027-01-05", False),
        ("", "needs_review", None, True),
        ("The contract was signed on 15 October 2026.", "needs_review", None, True),
        ("Hearing postponed to 32 October 2026.", "needs_review", None, True),
    ],
)
def test_representative_extraction_cases(text, status, event_date, requires_review):
    result = extract_hearing_update(text)

    assert result["status"] == status
    assert result["event_date"] == event_date
    assert result["requires_human_review"] is requires_review
    assert result["source_ref"] == "fixture:update-001"
