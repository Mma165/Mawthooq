from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


CaseType = Literal[
    "commercial_dispute",
    "employment",
    "contract",
    "debt",
    "other",
]
CaseStage = Literal[
    "complaint",
    "initial_review",
    "evidence",
    "hearing",
    "judgment",
    "appeal",
    "other",
]


class CaseCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    case_type: CaseType
    description: str = Field(min_length=10, max_length=5000)
    current_stage: CaseStage
    lawyer_proposed_action: str | None = Field(default=None, max_length=2000)


class CaseResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    case_type: CaseType
    description: str
    current_stage: CaseStage
    status: Literal["active", "closed"]
    lawyer_proposed_action: str | None
    created_at: datetime
