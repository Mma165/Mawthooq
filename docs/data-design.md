# Mawthooq Data Design

PostgreSQL is the durable case memory. Uploaded binaries belong in S3-compatible object storage, not in database rows. `pgvector` stores embeddings for approved legal sources and searchable case-document chunks.

## Entities

| Entity | Important fields | Relationship |
| --- | --- | --- |
| Organization | id, name, created_at | Owns users and cases |
| User | id, organization_id, role, email | Belongs to one organization |
| Case | id, organization_id, type, description, current_stage, status, created_at | Owns updates, documents, events, assessments |
| CaseUpdate | id, case_id, author_id, text, source_type, received_at, created_at | Immutable user or notification update |
| Document | id, case_id, storage_key, filename, mime_type, sha256, processing_status | Points to object storage |
| DocumentVersion | id, document_id, version, extracted_text, extraction_quality, created_at | Stores extraction history |
| ExtractedFact | id, document_version_id, fact_type, value, page, confidence | Provenance for normalized facts |
| CaseEvent | id, case_id, event_type, stage, event_date, source_ref, confidence | Builds the case journey |
| LegalSource | id, title, source_type, jurisdiction, effective_date, url, content, embedding | Curated retrieval corpus |
| Assessment | id, case_id, ranges, strengths, risks, assumptions, citations, confidence, model_version | Timestamped AI result |
| Recommendation | id, assessment_id, action, rationale, citations | Proposed next step, never automatic action |
| Verification | id, recommendation_id, reviewer_id, decision, comments, reviewed_at | Human verification record |
| Checklist | id, case_id, recommendation_id, items, created_at | Required documents for preparation |
| Draft | id, case_id, checklist_id, content, status, created_at | Review-only filing preparation |
| Review | id, case_id, reviewer_id, decision, evidence_reviewed, comments, created_at | Append-only human review |
| AuditEvent | id, organization_id, user_id, action, resource_type, resource_id, created_at | Access and state-change audit trail |

## Relationships

```text
Organization 1--* User
Organization 1--* Case
Case 1--* CaseUpdate
Case 1--* Document 1--* DocumentVersion 1--* ExtractedFact
Case 1--* CaseEvent
Case 1--* Assessment 1--* Recommendation 1--* Verification
Case 1--* Checklist 1--* Draft
Case 1--* Review
Organization 1--* AuditEvent
LegalSource is retrieved by Assessment and Recommendation citations
```

## Processing states

Documents and assessments use `uploaded`, `extracting`, `indexed`, `ready`, `failed`, and `needs_review`. State transitions are recorded in audit events. Failed processing preserves the original case data and exposes a repair/retry path.

## Access and retention

- Every case query is scoped by authenticated `organization_id`.
- Users may access only cases allowed by their organization role.
- Original binaries use private object-storage keys and time-limited access URLs.
- Extracted text and AI outputs require a retention decision because they may contain confidential legal information.
- Do not retain raw prompts, duplicate binaries, unused personal data, or unproven AI outputs indefinitely.
- Reviews and audit events are append-only; corrections create a new record rather than erasing history.
- Secrets and API keys are environment configuration, never database content or source code.
