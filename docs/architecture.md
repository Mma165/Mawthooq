# Mawthooq Architecture

## Development topology

```text
Business user
    |
    v
React/Vite frontend :3000
    |
    v
FastAPI backend :8000
    |-----------------------> PostgreSQL + pgvector :5432
    |
    +-----------------------> Local private upload storage (development)
    |
    +-----------------------> AI/document pipeline (future)
```

The backend is the system boundary. The browser never calls an AI provider or database directly. The frontend renders state returned by the backend and owns presentation, forms, upload progress, timeline views, and human-review interactions.

## Current environment

The initial Compose stack contains:

- `frontend`: Vite development server and React shell.
- `backend`: FastAPI application with `/health` and `/health/database`.
- `db`: PostgreSQL 16 with the `pgvector` extension image.

Uploaded binaries are stored during development in the ignored `backend/uploads/`
directory using generated UUID filenames. PostgreSQL stores document metadata and
processing status. Production object storage, malware scanning, and access control
are still required before handling real customer data.

The database has a named Docker volume so local data survives a normal `docker compose down`.

## Planned case-analysis flow

1. A business user creates a case or adds a document update in the frontend.
2. The backend validates access, stores case metadata, and stores the original binary in object storage.
3. A background process extracts text, uses OCR when needed, and records page/section provenance.
4. Legal-source and case-document chunks are retrieved using jurisdiction metadata and semantic search.
5. The AI pipeline returns structured analysis with citations, assumptions, uncertainty, and a human-review flag.
6. The backend persists the assessment and timeline event.
7. The frontend presents the journey and decision-support information; it never submits a legally binding action.

## Design rules

- Case updates are timestamped and traceable to their source document or user entry.
- AI output is an estimate and decision support, never a guarantee or judge prediction.
- Every generated claim must have a case-document or legal-source reference.
- Conflicting sources, missing evidence, low confidence, high financial impact, and binding proposed actions require human review.
- Direct court-system integration and automatic filing are outside the MVP.

## Implemented legal-source retrieval

Approved downloaded Saudi PDFs are ingested only by an explicit backend CLI command.
The command verifies download-manifest hashes, persists source/page/chunk provenance,
and stores pgvector embeddings. Case-document retrieval remains under `/api/search`;
approved legal-source retrieval is separate at `/api/legal-sources/search` and requires
a jurisdiction filter. Assessment generation is not part of this retrieval slice.
