from uuid import UUID

from fastapi import APIRouter, HTTPException, status
import psycopg

from app import services
from app.schemas import CaseCreate, CaseResponse


router = APIRouter(prefix="/api/cases", tags=["cases"])


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
