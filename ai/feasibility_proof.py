"""Provider-free Day 2 proof for extracting a case event from an update."""

import json
import re


SAMPLE_UPDATE = "Hearing postponed to 15 October 2026."


def extract_hearing_update(text: str) -> dict[str, object]:
    match = re.search(
        r"hearing\s+postponed\s+to\s+(\d{1,2})\s+([A-Za-z]+)\s+(\d{4})",
        text,
        re.IGNORECASE,
    )
    if match is None:
        return {
            "status": "needs_review",
            "event_type": None,
            "event_date": None,
            "stage": None,
            "source_ref": "fixture:update-001",
            "requires_human_review": True,
            "review_reasons": ["No supported hearing-postponement pattern found"],
        }

    day, month_name, year = match.groups()
    month_number = {
        "january": "01",
        "february": "02",
        "march": "03",
        "april": "04",
        "may": "05",
        "june": "06",
        "july": "07",
        "august": "08",
        "september": "09",
        "october": "10",
        "november": "11",
        "december": "12",
    }[month_name.lower()]
    return {
        "status": "ready",
        "event_type": "hearing_postponed",
        "event_date": f"{year}-{month_number}-{int(day):02d}",
        "stage": "hearing",
        "source_ref": "fixture:update-001",
        "requires_human_review": False,
        "review_reasons": [],
    }


if __name__ == "__main__":
    print(json.dumps(extract_hearing_update(SAMPLE_UPDATE), indent=2))
