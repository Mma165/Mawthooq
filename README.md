# Mawthooq

Mawthooq is an AI-powered legal case intelligence platform for businesses. It helps decision-makers understand what is happening in a case, what comes next, why an action is recommended, and what should be verified with their lawyer.

This repository currently contains the Day 2 development foundation. It is intentionally not a complete legal product yet.

## Product boundaries

Mawthooq supports case understanding, document-based updates, grounded analysis, assessment ranges, preparation checklists, and human review. It does not replace lawyers, guarantee outcomes, submit filings, or connect directly to a court system in the MVP.

## Current stack

| Area | Technology | Purpose |
| --- | --- | --- |
| Frontend | React, Vite, JavaScript | Initial product shell and future case views |
| Backend | FastAPI, Python 3.12 | REST API and service boundary |
| Database | PostgreSQL 16 with pgvector | Persistent case memory and future semantic retrieval |
| Database driver | psycopg 3 | Backend database connectivity |
| Containers | Docker Compose | Reproducible local development |

The AI provider, document extraction pipeline, authentication, and product APIs will be added behind the backend boundary as the MVP is implemented.

## Repository structure

```text
.
├── backend/
│   ├── app/main.py       # FastAPI application and health routes
│   ├── requirements.txt  # Python dependencies
│   └── Dockerfile
├── frontend/
│   ├── src/               # React starter shell
│   ├── package.json
│   └── Dockerfile
├── docs/
│   └── architecture.md
├── .env.example
├── docker-compose.yml
└── README.md
```

## Prerequisites

- Docker Desktop with Docker Compose
- Git

No local Python, Node.js, or PostgreSQL installation is required for the Docker workflow.

## Start the environment

1. Clone the repository and open its directory.
2. Create a local environment file:

	```powershell
	Copy-Item .env.example .env
	```

	On macOS/Linux, use `cp .env.example .env`.

3. Start all services:

	```powershell
	docker compose up --build
	```

4. Open the frontend at <http://localhost:3000>.

The backend is available at <http://localhost:8000>. Interactive API documentation is available at <http://localhost:8000/docs>.

## Verify the environment

Run these commands in a second terminal while Compose is running:

```powershell
Invoke-RestMethod http://localhost:8000/health
Invoke-RestMethod http://localhost:8000/health/database
```

Expected results include `status: ok`. The database check confirms that the API can connect to PostgreSQL and that the `vector` extension is enabled during backend startup.

To inspect service status:

```powershell
docker compose ps
```

## Stop and reset

Stop containers while keeping database data:

```powershell
docker compose down
```

Stop containers and delete the local database volume:

```powershell
docker compose down -v
```

Use the second command only when you intentionally want a clean database.

## Configuration

`.env.example` lists the supported local variables. Copy it to `.env` and change the development database password if the environment is shared. Never commit `.env` or API keys. The Compose file supplies safe development defaults so the stack can start immediately.

## Development workflow

- Keep `main` stable.
- Create a focused feature branch for each task.
- Update the relevant documentation when an API or data contract changes.
- Open a pull request and get at least one teammate review before merging.
- Do not add direct court integration, automatic filing, or binding legal actions to the MVP without an explicit product decision.

## Troubleshooting

**Port already in use**: change `BACKEND_PORT`, `FRONTEND_PORT`, or `POSTGRES_PORT` in `.env`, then restart Compose. `VITE_API_BASE_URL` must match the host-facing backend port if the frontend calls the API from a browser.

**Backend exits while PostgreSQL starts**: run `docker compose logs db backend`. The backend waits for the database health check; retry after the database becomes healthy.

**Stale dependencies or build output**: rebuild with `docker compose build --no-cache`, then run `docker compose up`.

**Windows file sharing or Docker Desktop errors**: make sure the repository directory is available to Docker Desktop under Settings > Resources > File Sharing.

## Next implementation slices

1. Add organization, user, case, document, and case-event data models.
2. Add authenticated case intake and document upload endpoints.
3. Add document extraction with processing states and page-level provenance.
4. Add curated legal-source ingestion and pgvector retrieval.
5. Add structured assessment and human-review contracts.
