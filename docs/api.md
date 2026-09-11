# Mawthooq API Contract

This is the initial REST contract for the MVP. The backend owns authorization, validation, persistence, AI orchestration, and audit history. The frontend consumes these resources and never calls the model provider directly.

## Conventions

- Base path: `/api`
- IDs: UUID strings
- Timestamps: ISO 8601 UTC strings
- Upload and analysis work asynchronously.
- Every case belongs to an organization; authorization must verify organization membership before access.
- AI-derived responses include provenance and `requires_human_review`.

## Health

### `GET /health`

Used by Docker and operations to confirm that the API process is alive.

Response `200`:

```json
{"status":"ok","service":"mawthooq-api"}
```

### `GET /health/database`

Checks PostgreSQL connectivity and the `vector` extension.

Response `200`:

```json
{"status":"ok","database":"mawthooq"}
```

## Cases

### `GET /api/cases`

Returns persisted cases ordered from newest to oldest. This endpoint is intended for the business dashboard and currently has no authentication until organization access control is added.

Response `200`:

```json
[
  {
    "id": "case-uuid",
    "case_type": "commercial_dispute",
    "description": "Dispute concerning an unpaid supply contract.",
    "current_stage": "evidence",
    "status": "active",
    "lawyer_proposed_action": "Submit supporting payment records",
    "created_at": "2026-09-09T10:00:00Z"
  }
]
```

An empty database returns `[]`. Storage failures return `503`.

### `POST /api/cases`

Creates and persists a case profile. This is the first implemented MVP endpoint and is consumed by the case-intake screen.

Request:

```json
{
  "case_type": "commercial_dispute",
  "description": "Dispute concerning an unpaid supply contract.",
  "current_stage": "evidence",
  "lawyer_proposed_action": "Submit supporting payment records"
}
```

Response `201`:

```json
{
  "id": "case-uuid",
  "case_type": "commercial_dispute",
  "description": "Dispute concerning an unpaid supply contract.",
  "current_stage": "evidence",
  "status": "active",
  "lawyer_proposed_action": "Submit supporting payment records",
  "created_at": "2026-09-09T10:00:00Z"
}
```

Validation errors return `422` for a missing/short description, unsupported case type or stage, oversized fields, or unknown request fields. Storage failures return `503`.

### `GET /api/cases/{case_id}`

Returns a persisted case profile by UUID. It returns `404` when the case does not exist, `422` for an invalid UUID, and `503` when storage is unavailable.

## Case values

Supported `case_type` values are `commercial_dispute`, `employment`, `contract`, `debt`, and `other`.

Supported `current_stage` values are `complaint`, `initial_review`, `evidence`, `hearing`, `judgment`, `appeal`, and `other`.

### `POST /api/cases/{case_id}/updates`

Adds an immutable user-provided update or official notification. It does not overwrite earlier history.

Request:

```json
{
  "text": "Hearing postponed to 15 October 2026.",
  "source_type": "official_notification",
  "received_at": "2026-09-09T10:10:00Z"
}
```

Response `202`:

```json
{
  "id": "update-uuid",
  "case_id": "case-uuid",
  "processing_status": "extracting",
  "created_at": "2026-09-09T10:10:00Z"
}
```

Errors: `400`, `401`, `403`, `404`, `422` unsupported content.

### `GET /api/cases/{case_id}/timeline`

Returns completed, current, and expected case events. Each event includes its source reference and confidence.

Response `200`:

```json
{
  "case_id": "case-uuid",
  "events": [
    {
      "id": "event-uuid",
      "stage": "hearing",
      "label": "Hearing postponed",
      "event_date": "2026-10-15",
      "state": "current",
      "source_refs": ["document-uuid:p1"]
    }
  ]
}
```

## Documents

### `POST /api/cases/{case_id}/documents`

Accepts PDF, DOCX, or supported image files. The development implementation validates
and stores the binary in private local storage, then extracts page text and persists
page provenance. Text-native documents normally transition to `ready`; scanned or
poorly extracted documents transition to `needs_review`; malformed documents become
`failed`. The MVP never treats an uploaded document as trusted instructions.

Response `202`:

```json
{
  "id": "document-uuid",
  "case_id": "case-uuid",
  "filename": "hearing-notice.pdf",
  "processing_status": "uploaded",
  "created_at": "2026-09-09T10:20:00Z"
}
```

Errors: `400` unsupported format, empty content, or invalid file signature, `404` missing
case, `413` too large, and `503` when document metadata storage is unavailable.

### `GET /api/documents/{document_id}/status`

Response `200`:

```json
{
  "id": "document-uuid",
  "processing_status": "ready",
  "extracted_page_count": 2,
  "requires_human_review": false,
  "error": null
}
```

Allowed states: `uploaded`, `extracting`, `indexed`, `ready`, `failed`, `needs_review`.

### `POST /api/documents/{document_id}/index`

Chunks the persisted page text, generates embeddings with the configured Ollama
embedding model, stores vectors in pgvector, and changes the document status to
`indexed`. The embedding model must be available in Ollama; otherwise the endpoint
returns `503` and the document is not presented as searchable.

### `GET /api/search?query=...&limit=5`

Embeds an Arabic or English query and returns ranked chunks with document IDs,
page numbers, distances, and citations in the form `document-uuid:pN`. This is a
retrieval endpoint only; it does not generate a legal conclusion.

## Legal sources

### `GET /api/legal-sources/search?query=...&jurisdiction=Saudi%20Arabia&case_category=contract&limit=5`

Searches explicitly ingested, approved legal-source PDF chunks. `jurisdiction` is
required and `case_category` is optional; both are metadata filters applied before
ranking. A blank query, unsupported category, or limit outside 1–20 is rejected
before the embedding provider is called. Results include the official source
metadata, matched page text, similarity distance, and a `source-id:pN` citation.
This endpoint returns retrieval evidence only and never produces a legal conclusion.

## Assessments

### `POST /ai/feasibility`

Day 2 live-provider proof endpoint. It accepts one representative case update and asks the configured local Ollama model to extract only explicitly stated facts. Gemini remains an optional provider. This endpoint is a feasibility proof, not the final case-analysis workflow.

Request:

```json
{"update_text":"Hearing postponed to 15 October 2026."}
```

Response `200` with a configured provider includes the model name, structured model result, and `requires_human_review: true`. Without a key, it returns `status: needs_configuration`. Empty input returns `status: invalid_input`.

### `POST /api/cases/{case_id}/assessments`

Starts a new assessment using the persisted case, document facts, timeline, proposed action, and retrieved legal sources.

Response `202`:

```json
{
  "id": "assessment-uuid",
  "case_id": "case-uuid",
  "processing_status": "extracting",
  "requires_human_review": true
}
```

### `GET /api/assessments/{assessment_id}`

Response `200`:

```json
{
  "id": "assessment-uuid",
  "favorable_outcome": {"low": 0.55, "high": 0.68, "unit": "probability"},
  "resolution_time": {"low": 8, "high": 14, "unit": "months"},
  "evidence_strength": "moderate",
  "strengths": ["Signed contract"],
  "risks": ["Missing payment records"],
  "assumptions": ["The contract copy is complete"],
  "uncertainties": ["Opposing response has not been received"],
  "confidence": {"level": "medium", "basis": ["source_coverage", "extraction_quality"]},
  "citations": [{"source_id": "document-uuid", "location": "page 2", "quote": "..."}],
  "requires_human_review": true,
  "model_version": "provider-adapter-v0",
  "created_at": "2026-09-09T10:30:00Z"
}
```

The result is an estimate for decision support, never a judge prediction.

## Lawyer action verification

### `POST /api/cases/{case_id}/action-verifications`

Analyzes a proposed action and returns procedural basis, required information, relevant sources, and questions for the lawyer. It cannot approve or submit the action.

Request:

```json
{"proposed_action":"File an appeal"}
```

Response `202` includes `processing_status`, `procedural_basis`, `required_information`, `questions_to_verify`, `citations`, and `requires_human_review`.

## Preparation and review

- `POST /api/cases/{case_id}/checklists` creates a required-document checklist.
- `POST /api/cases/{case_id}/drafts` creates a review-only filing draft. It never submits it.
- `POST /api/reviews` records an append-only human review with reviewer, decision, evidence reviewed, and comments.
- `GET /api/reviews/{review_id}` returns the review record.

These endpoints return `401`, `403`, `404`, `409` for invalid workflow state, and `422` for invalid input as appropriate.

## Error shape

All API errors should use a consistent shape:

```json
{
  "error": {
    "code": "insufficient_evidence",
    "message": "A reliable assessment cannot be completed.",
    "details": ["No document supports the proposed deadline."]
  }
}
```
