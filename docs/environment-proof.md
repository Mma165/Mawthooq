# Environment Proof

## Day 2 checks

Run from the repository root while Docker Desktop is running:

```powershell
docker compose up --build
```

In a second terminal:

```powershell
Invoke-RestMethod http://localhost:8000/health
Invoke-RestMethod http://localhost:8000/health/database
docker compose ps
```

Open `http://localhost:3000` and confirm the React starter shell renders.

## Expected evidence

- `frontend` is running and renders the Mawthooq shell.
- `backend` returns `{ "status": "ok", "service": "mawthooq-api" }`.
- `backend/health/database` returns status `ok` and database `mawthooq`.
- `db` is healthy in `docker compose ps`.
- FastAPI documentation is available at `http://localhost:8000/docs`.
- PostgreSQL starts with the `vector` extension enabled.

## AI proof status

The Day 2 AI proof is documented in `docs/ai-contract.md`. It is intentionally deterministic and provider-free so every teammate can run the environment without an API key. The live LLM/provider adapter, OCR, retrieval corpus, and assessment generation are Day 3 implementation work.

## Seven-minute review order

1. Product and MVP boundaries: business visibility, not lawyer replacement.
2. Architecture: browser -> API -> database/object storage -> AI pipeline.
3. API and AI contracts: asynchronous processing, structured outputs, citations, uncertainty.
4. Environment proof: frontend, backend, database, Docker.
5. Feasibility proof: representative hearing-postponement update.
6. Risks: legal sources, grounding, privacy, extraction, prompt injection, cost.
7. Day 3 ownership and first tasks.
