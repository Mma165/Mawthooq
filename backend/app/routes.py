import json
from uuid import UUID

from fastapi import APIRouter, File, HTTPException, UploadFile, status
from fastapi.responses import StreamingResponse
import psycopg

from app import services
from app.schemas import (
    AssessmentResponse,
    CaseCreate,
    CaseResponse,
    ChatMessageResponse,
    ChatRequest,
    DocumentStatusResponse,
    DocumentUploadResponse,
)


router = APIRouter(prefix="/api/cases", tags=["cases"])
document_router = APIRouter(prefix="/api/documents", tags=["documents"])
search_router = APIRouter(prefix="/api/search", tags=["search"])
legal_source_router = APIRouter(prefix="/api/legal-sources", tags=["legal sources"])


@router.get("", response_model=list[CaseResponse])
def list_cases() -> list[CaseResponse]:
    try:
        return services.list_cases()
    except psycopg.Error as error:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Case storage is temporarily unavailable.",
        ) from error


@router.post("", response_model=CaseResponse, status_code=status.HTTP_201_CREATED)
def create_case(case: CaseCreate) -> CaseResponse:
    try:
        return services.create_case(case)
    except psycopg.Error as error:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Case storage is temporarily unavailable.",
        ) from error


@router.get("/{case_id}", response_model=CaseResponse)
def get_case(case_id: UUID) -> CaseResponse:
    try:
        case = services.get_case(case_id)
    except psycopg.Error as error:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Case storage is temporarily unavailable.",
        ) from error
    if case is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Case not found.")
    return case


@router.post("/{case_id}/documents", response_model=DocumentUploadResponse, status_code=status.HTTP_202_ACCEPTED)
async def upload_case_document(case_id: UUID, file: UploadFile = File(...)) -> DocumentUploadResponse:
    try:
        return await services.upload_document(case_id, file)
    except services.UploadError as error:
        raise HTTPException(status_code=error.status_code, detail=str(error)) from error
    except psycopg.Error as error:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Case storage is temporarily unavailable.",
        ) from error


@document_router.get("/{document_id}/status", response_model=DocumentStatusResponse)
def document_status(document_id: UUID) -> DocumentStatusResponse:
    try:
        document = services.get_document_status(document_id)
    except psycopg.Error as error:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Document storage is temporarily unavailable.",
        ) from error
    if document is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found.")
    return document


@document_router.post("/{document_id}/index")
def index_document(document_id: UUID) -> dict[str, object]:
    try:
        chunk_count = services.index_document(document_id)
        return {"document_id": document_id, "status": "indexed", "chunk_count": chunk_count}
    except services.UploadError as error:
        raise HTTPException(status_code=error.status_code, detail=str(error)) from error
    except (psycopg.Error, ValueError) as error:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Document indexing is unavailable.",
        ) from error


@router.post("/{case_id}/assessments", response_model=AssessmentResponse, status_code=status.HTTP_201_CREATED)
def create_assessment(case_id: UUID) -> AssessmentResponse:
    try:
        return services.generate_assessment(case_id)
    except services.UploadError as error:
        raise HTTPException(status_code=error.status_code, detail=str(error)) from error
    except (psycopg.Error, ValueError, RuntimeError) as error:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Case assessment is unavailable.",
        ) from error


@router.get("/{case_id}/assessments", response_model=list[AssessmentResponse])
def get_assessments(case_id: UUID) -> list[AssessmentResponse]:
    try:
        return services.list_assessments(case_id)
    except services.UploadError as error:
        raise HTTPException(status_code=error.status_code, detail=str(error)) from error
    except psycopg.Error as error:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Case storage is temporarily unavailable.",
        ) from error


@router.post("/{case_id}/chat")
def chat_with_case(case_id: UUID, payload: ChatRequest) -> dict[str, object]:
    try:
        return services.chat_with_case(case_id, payload.message)
    except services.UploadError as error:
        raise HTTPException(status_code=error.status_code, detail=str(error)) from error
    except (psycopg.Error, ValueError, RuntimeError) as error:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Case chat is unavailable.",
        ) from error


@router.post("/{case_id}/chat/stream")
def chat_stream(case_id: UUID, payload: ChatRequest):
    try:
        prepared = services.prepare_chat_stream(case_id, payload.message)
    except services.UploadError as error:
        raise HTTPException(status_code=error.status_code, detail=str(error)) from error
    except (psycopg.Error, ValueError) as error:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Case chat is unavailable.",
        ) from error

    def event_stream():
        try:
            yield "data: " + json.dumps(
                {"type": "user", "message": prepared["user_message"]},
                ensure_ascii=False, default=str,
            ) + "\n\n"
            for event in services.stream_chat_reply(prepared):
                yield "data: " + json.dumps(event, ensure_ascii=False, default=str) + "\n\n"
        except (psycopg.Error, ValueError, RuntimeError):
            yield "data: " + json.dumps(
                {"type": "error", "detail": "Case chat is unavailable."},
                ensure_ascii=False,
            ) + "\n\n"

    return StreamingResponse(event_stream(), media_type="text/event-stream")


@router.get("/{case_id}/messages", response_model=list[ChatMessageResponse])
def get_case_messages(case_id: UUID) -> list[ChatMessageResponse]:
    try:
        return services.list_case_messages(case_id)
    except services.UploadError as error:
        raise HTTPException(status_code=error.status_code, detail=str(error)) from error
    except psycopg.Error as error:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Case storage is temporarily unavailable.",
        ) from error


@search_router.get("")
def search_documents(query: str, limit: int = 5) -> dict[str, object]:
    if limit < 1 or limit > 20:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="limit must be between 1 and 20.")
    try:
        return {"query": query, "results": services.search_documents(query, limit)}
    except services.UploadError as error:
        raise HTTPException(status_code=error.status_code, detail=str(error)) from error
    except (psycopg.Error, ValueError) as error:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Document search is unavailable.") from error


@legal_source_router.get("/search")
def search_legal_sources(query: str, jurisdiction: str, case_category: str | None = None, limit: int = 5) -> dict[str, object]:
    if limit < 1 or limit > 20:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="limit must be between 1 and 20.")
    try:
        return {
            "query": query,
            "jurisdiction": jurisdiction,
            "case_category": case_category,
            "results": services.search_legal_sources(query, jurisdiction, case_category, limit),
        }
    except services.UploadError as error:
        raise HTTPException(status_code=error.status_code, detail=str(error)) from error
    except (psycopg.Error, ValueError) as error:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Legal-source search is unavailable.") from error
