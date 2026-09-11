from datetime import datetime, timezone
from io import BytesIO
from pathlib import Path
from uuid import uuid4

import pytest
from fastapi import UploadFile

from app import services


@pytest.fixture
def upload_directory(tmp_path, monkeypatch):
    monkeypatch.setattr(services, "UPLOAD_DIR", str(tmp_path))
    monkeypatch.setattr(services, "MAX_UPLOAD_BYTES", 1024)
    return tmp_path


def make_upload(content: bytes, filename: str, content_type: str) -> UploadFile:
    return UploadFile(BytesIO(content), filename=filename, headers={"content-type": content_type})


def test_pdf_upload_is_stored_with_safe_generated_name(upload_directory, monkeypatch):
    case_id = uuid4()
    document_id = uuid4()
    monkeypatch.setattr(services.repositories, "case_exists", lambda _: True)
    monkeypatch.setattr(services.repositories, "update_document_processing", lambda *_: None)
    monkeypatch.setattr(services.repositories, "replace_document_pages", lambda *_: None)
    monkeypatch.setattr(services, "uuid4", lambda: document_id)
    monkeypatch.setattr(
        services.repositories,
        "create_document",
        lambda document: {
            **document,
            "original_filename": document["original_filename"],
            "processing_status": "uploaded",
            "created_at": datetime.now(timezone.utc),
        },
    )

    result = __import__("asyncio").run(
        services.upload_document(
            case_id,
            make_upload(b"%PDF-1.7\ncase evidence", "../../secret.pdf", "application/pdf"),
        )
    )

    assert result["filename"] == "secret.pdf"
    assert result["processing_status"] == "failed"
    stored_files = list(upload_directory.iterdir())
    assert len(stored_files) == 1
    assert stored_files[0].name == f"{document_id}.pdf"


def test_wrong_signature_is_rejected(upload_directory, monkeypatch):
    monkeypatch.setattr(services.repositories, "case_exists", lambda _: True)

    with pytest.raises(services.UploadError, match="does not match"):
        __import__("asyncio").run(
            services.upload_document(
                uuid4(), make_upload(b"not a pdf", "notice.pdf", "application/pdf")
            )
        )
    assert list(upload_directory.iterdir()) == []


def test_upload_over_limit_is_rejected_and_cleaned(upload_directory, monkeypatch):
    monkeypatch.setattr(services.repositories, "case_exists", lambda _: True)

    with pytest.raises(services.UploadError) as error:
        __import__("asyncio").run(
            services.upload_document(
                uuid4(), make_upload(b"%PDF-1.7\n" + b"x" * 1024, "large.pdf", "application/pdf")
            )
        )

    assert error.value.status_code == 413
    assert list(upload_directory.iterdir()) == []


def test_missing_case_is_rejected(upload_directory, monkeypatch):
    monkeypatch.setattr(services.repositories, "case_exists", lambda _: False)

    with pytest.raises(services.UploadError) as error:
        __import__("asyncio").run(
            services.upload_document(
                uuid4(), make_upload(b"%PDF-1.7", "notice.pdf", "application/pdf")
            )
        )

    assert error.value.status_code == 404


def test_metadata_failure_removes_binary(upload_directory, monkeypatch):
    monkeypatch.setattr(services.repositories, "case_exists", lambda _: True)
    def fail_insert(_):
        raise RuntimeError("database write failed")
    monkeypatch.setattr(services.repositories, "create_document", fail_insert)

    with pytest.raises(RuntimeError):
        __import__("asyncio").run(
            services.upload_document(
                uuid4(), make_upload(b"%PDF-1.7", "notice.pdf", "application/pdf")
            )
        )

    assert list(upload_directory.iterdir()) == []
