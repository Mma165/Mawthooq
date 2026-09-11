import hashlib
import tempfile
from pathlib import Path
from uuid import UUID, uuid4

from fastapi import UploadFile

from app.config import ALLOWED_UPLOAD_TYPES, MAX_UPLOAD_BYTES, UPLOAD_DIR
from app.extraction import extract_document
from app.rag import chunk_page, embed_text

from app import repositories
from app.schemas import CASE_TYPES, CaseCreate


class UploadError(Exception):
    def __init__(self, message: str, status_code: int = 400):
        super().__init__(message)
        self.status_code = status_code


def create_case(case: CaseCreate) -> dict[str, object]:
    return repositories.create_case(case)


def get_case(case_id: UUID) -> dict[str, object] | None:
    return repositories.get_case(case_id)


def list_cases() -> list[dict[str, object]]:
    return repositories.list_cases()


def _matches_signature(mime_type: str, header: bytes, path: Path) -> bool:
    if mime_type == "application/pdf":
        return header.startswith(b"%PDF-")
    if mime_type == "application/vnd.openxmlformats-officedocument.wordprocessingml.document":
        import zipfile

        try:
            with zipfile.ZipFile(path) as archive:
                names = set(archive.namelist())
            return "[Content_Types].xml" in names and any(name.startswith("word/") for name in names)
        except zipfile.BadZipFile:
            return False
    signatures = {
        "image/jpeg": header.startswith(b"\xff\xd8\xff"),
        "image/png": header.startswith(b"\x89PNG\r\n\x1a\n"),
        "image/webp": header.startswith(b"RIFF") and header[8:12] == b"WEBP",
        "image/gif": header.startswith((b"GIF87a", b"GIF89a")),
    }
    return signatures.get(mime_type, False)


async def upload_document(case_id: UUID, upload: UploadFile) -> dict[str, object]:
    if not repositories.case_exists(case_id):
        raise UploadError("Case not found.", 404)
    mime_type = upload.content_type or ""
    if mime_type not in ALLOWED_UPLOAD_TYPES:
        raise UploadError("Unsupported document type.")
    filename = Path(upload.filename or "document").name
    if not filename or len(filename) > 255:
        raise UploadError("Filename must be between 1 and 255 characters.")

    upload_dir = Path(UPLOAD_DIR)
    upload_dir.mkdir(parents=True, exist_ok=True)
    document_id = uuid4()
    temporary_path: Path | None = None
    try:
        with tempfile.NamedTemporaryFile(dir=upload_dir, prefix=".upload-", delete=False) as temporary:
            temporary_path = Path(temporary.name)
            digest = hashlib.sha256()
            total = 0
            first_chunk = b""
            while chunk := await upload.read(1024 * 1024):
                if not first_chunk:
                    first_chunk = chunk[:512]
                total += len(chunk)
                if total > MAX_UPLOAD_BYTES:
                    raise UploadError("Document exceeds the 10 MiB upload limit.", 413)
                digest.update(chunk)
                temporary.write(chunk)
        if total == 0:
            raise UploadError("Document cannot be empty.")
        if not _matches_signature(mime_type, first_chunk, temporary_path):
            raise UploadError("Document content does not match its declared type.")

        storage_path = upload_dir / f"{document_id}{ALLOWED_UPLOAD_TYPES[mime_type]}"
        metadata = repositories.create_document({
            "id": document_id,
            "case_id": case_id,
            "original_filename": filename,
            "mime_type": mime_type,
            "size_bytes": total,
            "sha256": digest.hexdigest(),
            "storage_path": storage_path.name,
        })
        temporary_path.replace(storage_path)
        repositories.update_document_processing(document_id, "extracting")
        try:
            extraction = extract_document(storage_path, mime_type)
            repositories.replace_document_pages(
                document_id,
                [
                    {
                        "page_number": page.page_number,
                        "text": page.text,
                        "language": page.language,
                        "extraction_method": page.extraction_method,
                        "quality": page.quality,
                    }
                    for page in extraction.pages
                ],
            )
            repositories.update_document_processing(
                document_id,
                extraction.status,
                "; ".join(extraction.review_reasons) or None,
            )
            metadata["processing_status"] = extraction.status
        except Exception as error:
            reason = f"Document extraction failed: {type(error).__name__}"
            repositories.update_document_processing(document_id, "failed", reason)
            metadata["processing_status"] = "failed"
        return {
            "id": metadata["id"], "case_id": metadata["case_id"], "filename": metadata["original_filename"],
            "mime_type": metadata["mime_type"], "size_bytes": metadata["size_bytes"], "sha256": metadata["sha256"],
            "processing_status": metadata["processing_status"], "created_at": metadata["created_at"],
        }
    finally:
        if temporary_path and temporary_path.exists():
            temporary_path.unlink()


def get_document_status(document_id: UUID) -> dict[str, object] | None:
    document = repositories.get_document(document_id)
    if document is None:
        return None
    return {
        "id": document["id"], "case_id": document["case_id"], "filename": document["original_filename"],
        "processing_status": document["processing_status"],
        "requires_human_review": document["processing_status"] != "ready",
        "error": document["error"], "created_at": document["created_at"],
    }


def index_document(document_id: UUID) -> int:
    document = repositories.get_document(document_id)
    if document is None:
        raise UploadError("Document not found.", 404)
    pages = repositories.get_document_pages(document_id)
    chunks = []
    for page in pages:
        for chunk in chunk_page(page["text"], page["page_number"]):
            chunk["embedding"] = embed_text(chunk["text"])
            chunks.append(chunk)
    if not chunks:
        raise UploadError("Document has no usable text to index.")
    repositories.replace_document_chunks(document_id, chunks)
    repositories.update_document_processing(document_id, "indexed")
    return len(chunks)


def search_documents(query: str, limit: int = 5) -> list[dict[str, object]]:
    normalized_query = query.strip()
    if not normalized_query:
        raise UploadError("Search query is required.")
    results = repositories.search_document_chunks(embed_text(normalized_query), limit)
    return [
        {
            "document_id": result["document_id"],
            "page_number": result["page_number"],
            "chunk_index": result["chunk_index"],
            "text": result["text"],
            "citation": f"{result['document_id']}:p{result['page_number']}",
            "distance": result["distance"],
        }
        for result in results
    ]


def search_legal_sources(query: str, jurisdiction: str, case_category: str | None, limit: int = 5) -> list[dict[str, object]]:
    normalized_query = query.strip()
    if not normalized_query:
        raise UploadError("Search query is required.")
    normalized_jurisdiction = jurisdiction.strip()
    if not normalized_jurisdiction:
        raise UploadError("jurisdiction is required.")
    if case_category is not None and case_category not in CASE_TYPES:
        raise UploadError("case_category is not supported.", 422)
    results = repositories.search_legal_source_chunks(
        embed_text(normalized_query), normalized_jurisdiction, case_category, limit
    )
    return [
        {
            **result,
            "citation": f"{result['source_id']}:p{result['page_number']}",
        }
        for result in results
    ]
