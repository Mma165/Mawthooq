# Mawthooq Day 3 Plan

## Day 3 goal

Build a clean backend foundation around one real MVP flow: a business user creates a legal case and receives a validated case profile. The backend must run, persist the minimum case data, expose a stable API, and provide a replaceable AI service boundary.

Day 3 is not the day to finish the dashboard, full document processing, RAG, authentication, or the complete assessment workflow.

## First user flow

```text
Frontend case-intake form
    -> POST /api/cases
    -> FastAPI validation
    -> Case service
    -> PostgreSQL case record
    -> validated case response
    -> frontend confirmation
```

The existing `POST /ai/feasibility` endpoint remains a separate AI proof. It is not the main persisted product endpoint yet.

## Acceptance criteria

By the end of Day 3:

- The backend starts using the README commands.
- `GET /health` returns `200`.
- `GET /health/database` returns `200`.
- `POST /api/cases` accepts a valid case and returns `201`.
- Invalid or incomplete case input returns `422` with understandable validation details.
- A created case can be read back with `GET /api/cases/{case_id}`.
- The case record is stored in PostgreSQL.
- The database layer is isolated from route code.
- The AI provider is called through a service boundary, not directly from the route.
- At least one valid and two invalid/edge requests are demonstrated.
- README and API documentation describe the implemented behavior.
- Day 4 blockers and handoff items are recorded.

## Ownership

### Amr: backend

1. Create the backend structure: `config`, `routes`, `schemas`, `models`, `repositories`, and `services`.
2. Add the minimum database model for `Case`.
3. Add `POST /api/cases` and `GET /api/cases/{case_id}`.
4. Validate case type, description, current stage, and optional lawyer action.
5. Add understandable error responses and tests.
6. Keep `/health` and `/health/database` working.

### Mahmoud Ali, Ahmed Hatem, and Asiyah: AI/data

1. Keep the Ollama feasibility proof working.
2. Test three representative updates, including a clear update, incomplete information, and a conflicting or ambiguous update.
3. Record output quality, latency, missing citations, and incorrect assumptions.
4. Define the AI service input/output adapter that the backend can call later.
5. Do not add RAG, OCR, or complex prompting to the stable backend today.
6. Prepare the first legal-source fixture and document its jurisdiction and source metadata.

### Aya Hegazy: frontend

1. Prepare the case-intake form using the documented API contract.
2. Add fields for case type, description, current stage, and proposed lawyer action.
3. Add loading, success, validation-error, and server-error states.
4. Use a temporary mock response or the real endpoint after Amr publishes it.
5. Keep the existing Case -> Journey -> Intelligence -> Decision direction.

### Full team

1. Review the API request and response before implementation diverges.
2. Use feature branches and pull requests.
3. Test the same valid and invalid examples.
4. Confirm that no endpoint submits filings or creates binding legal actions.
5. Prepare the seven-minute Day 3 demonstration.

## Backend implementation order

1. Confirm `POST /api/cases` as the first MVP endpoint.
2. Add typed Pydantic request and response schemas.
3. Add a minimal `Case` table/model with organization placeholder support.
4. Add database session/configuration code.
5. Add repository functions for create and read.
6. Add a case service that owns business logic.
7. Add routes that call the service.
8. Add validation and consistent error handling.
9. Add tests.
10. Update README and API documentation.

## Suggested first API contract

### `POST /api/cases`

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

Validation examples:

- Empty description: `422`.
- Unsupported case type: `422`.
- Unsupported current stage: `422`.
- Oversized description: `422`.
- Database failure: `503` with a safe error message.

## Minimal database decision

Persistence is required today because the first MVP flow is case creation and case memory. Implement only the `Case` model and the minimum migration/repository logic. Do not create every future table yet.

The existing PostgreSQL/pgvector container remains the database. The model should be ready to add `organization_id`, but full authentication and tenant authorization can follow in the next slice.

## AI service boundary

The route must not import Ollama or Gemini directly. Use a service interface such as:

```python
def analyze_case_update(update_text: str) -> dict[str, object]:
    ...
```

The current provider adapter may remain the implementation. A deterministic mock should be available for backend tests so tests do not require Ollama to be running.

## Tests to demonstrate

```text
GET /health                         -> 200
POST /api/cases valid payload       -> 201
POST /api/cases empty description   -> 422
POST /api/cases invalid stage       -> 422
GET /api/cases/{created_id}         -> 200
POST /ai/feasibility valid update   -> ready or safe provider error
```

## Day 4 handoff

Record:

- Endpoints implemented and tested.
- Database models and migrations created.
- AI provider behavior and remaining mock work.
- Frontend fields and API assumptions.
- Known blockers, especially authentication, document storage, OCR, and approved legal sources.
- The exact next endpoint, preferably `POST /api/cases/{case_id}/documents`.

## Seven-minute review

1. One minute: restate the Mawthooq MVP boundary.
2. Two minutes: show backend structure and database flow.
3. One minute: create a case through `POST /api/cases`.
4. One minute: show validation with an invalid request.
5. One minute: explain the AI provider boundary and Ollama feasibility proof.
6. One minute: show tests, commits, blockers, and Day 4 handoff.
