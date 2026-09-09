# Mawthooq

Mawthooq is an AI-powered legal case intelligence platform for businesses. It helps decision-makers understand what is happening in a case, what comes next, why an action is recommended, and what should be verified with their lawyer.

This repository contains the completed Day 2 development foundation. It is intentionally not a complete legal product yet; the next sprint adds the case workflow on top of this verified environment.

## Product boundaries

Mawthooq supports case understanding, document-based updates, grounded analysis, assessment ranges, preparation checklists, and human review. It does not replace lawyers, guarantee outcomes, submit filings, or connect directly to a court system in the MVP.

## Current stack

| Area | Technology | Purpose |
| --- | --- | --- |
| Frontend | React, Vite, JavaScript | Initial product shell and future case views |
| Backend | FastAPI, Python 3.12 | REST API and service boundary |
| Database | PostgreSQL 16 with pgvector | Persistent case memory and future semantic retrieval |
| Database driver | psycopg 3 | Backend database connectivity |
| Local LLM | Ollama, `llama3.2:3b` | Free local feasibility and development model |
| Containers | Docker Compose | Reproducible local development |

The backend uses Ollama by default. Gemini remains an optional provider selected with `LLM_PROVIDER=gemini`. Document extraction, authentication, and product APIs will be added behind the backend boundary as the MVP is implemented.

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
├── ai/
│   ├── feasibility_proof.py # Provider-free Day 2 AI proof
│   └── fixtures/
├── docs/
│   ├── architecture.md
│   ├── api.md
│   ├── ai-contract.md
│   ├── data-design.md
│   ├── environment-proof.md
│   ├── risk-register.md
│   └── backlog.md
├── .env.example
├── docker-compose.yml
└── README.md
```

## Prerequisites

- [Docker Desktop](https://www.docker.com/products/docker-desktop/) with Docker Compose
- [Git](https://git-scm.com/downloads)
- An internet connection for the first Docker image and Ollama model download
- At least 6 GB of free disk space for the local Ollama model and Docker images
- At least 8 GB RAM recommended when running Ollama locally

No local Python, Node.js, PostgreSQL, or separate Ollama installation is required for the Docker workflow. Ollama runs inside the project Docker container.

Useful official documentation:

- [Docker Desktop installation guide](https://docs.docker.com/desktop/setup/install/windows-install/)
- [Docker Compose getting started guide](https://docs.docker.com/compose/gettingstarted/)
- [Ollama model library](https://ollama.com/library)
- [Ollama Docker image documentation](https://hub.docker.com/r/ollama/ollama)

## Complete setup from zero

### 1. Open the repository

Clone the repository from your Git hosting URL, then open PowerShell in the repository root. The folder must contain `docker-compose.yml`:

```powershell
cd "D:\NTG internship\Mawthooq"
Get-ChildItem docker-compose.yml
```

If you already have the project folder, skip cloning. Otherwise, use:

```powershell
git clone <YOUR-REPOSITORY-URL>
cd Mawthooq
```

### 2. Create the local configuration

Create `.env` from the committed template. `.env` is ignored by Git and must never be committed:

	```powershell
	Copy-Item .env.example .env
	```

On macOS/Linux, use `cp .env.example .env`.

For the default free local setup, keep these values:

```env
LLM_PROVIDER=ollama
OLLAMA_BASE_URL=http://ollama:11434
OLLAMA_MODEL=llama3.2:3b
```

Do not add a Gemini key for the Ollama setup. Gemini is optional and is not required to run Mawthooq locally.

### 3. Build and start the containers

Run this command in the first terminal and leave it running:

```powershell
docker compose up --build
```

The first build downloads the Python and Node dependencies. The services are:

| Service | Address | Purpose |
| --- | --- | --- |
| Frontend | http://localhost:3000 | React/Vite interface |
| Backend | http://localhost:8000 | FastAPI REST API |
| API docs | http://localhost:8000/docs | Interactive Swagger documentation |
| PostgreSQL | localhost:5432 | Persistent case data and pgvector |
| Ollama | http://localhost:11434 | Local LLM service |

### 4. Download the local model

Open a second PowerShell window in the repository root and run this once:

```powershell
docker compose exec ollama ollama pull llama3.2:3b
```

The model is stored in the named `ollama_data` volume. You do not need to download it again unless that volume is deleted.

### 5. Confirm all containers are healthy

```powershell
docker compose ps
```

Expected services are `frontend`, `backend`, `db`, and `ollama`. The `db` service should show `healthy`.

### 6. Open the application

Open <http://localhost:3000> in a browser. The current screen is the Day 2 environment shell; the case dashboard is a later implementation slice.

The backend is available at <http://localhost:8000>. Interactive API documentation is available at <http://localhost:8000/docs>.

## Day 2 documentation

- [Architecture](docs/architecture.md)
- [API contract](docs/api.md)
- [AI contract](docs/ai-contract.md)
- [Data design](docs/data-design.md)
- [Environment proof](docs/environment-proof.md)
- [Risk register](docs/risk-register.md)
- [Day 3 backlog](docs/backlog.md)

Run the provider-free feasibility proof from the repository root. This checks the extraction contract without needing any model or API key:

```powershell
python ai/feasibility_proof.py
```

It parses the representative update `Hearing postponed to 15 October 2026.` and returns structured, traceable output without requiring an external AI key.

Run the live local Ollama proof while the containers are running:

```powershell
Invoke-RestMethod -Method Post `
	-Uri http://localhost:8000/ai/feasibility `
	-ContentType "application/json" `
	-Body '{"update_text":"Hearing postponed to 15 October 2026."}'
```

Expected response values include:

- `status`: `ready`
- `provider`: `ollama`
- `model`: `llama3.2:3b`
- result containing the hearing date
- `requires_human_review`: `True`

The outer human-review flag remains true by design. The model output is not a final legal conclusion.

### Optional Gemini provider

Gemini is optional. To use it instead, place the key only in local `.env`, set `LLM_PROVIDER=gemini`, set `GEMINI_MODEL`, rebuild the backend, and never put the key in source code, the frontend, Git, screenshots, or chat messages.

## Verify the environment

Run these commands in a second terminal while Compose is running:

```powershell
Invoke-RestMethod http://localhost:8000/health
Invoke-RestMethod http://localhost:8000/health/database
```

Expected results include `status: ok`. The database check confirms that the API can connect to PostgreSQL and that the `vector` extension is enabled during backend startup.

The expected health responses are:

```json
{"status":"ok","service":"mawthooq-api"}
{"status":"ok","database":"mawthooq"}
```

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

**Password authentication failed for user `mawthooq`**: PostgreSQL keeps its initial password in the named Docker volume. If `POSTGRES_PASSWORD` changed in `.env` after the first startup, reset the disposable local database with `docker compose down -v`, then run `docker compose up --build` again. This deletes only local development database data. If you need to preserve that data, restore the original password in `.env` instead.

**Stale dependencies or build output**: rebuild with `docker compose build --no-cache`, then run `docker compose up`.

**Ollama model is missing**: run `docker compose exec ollama ollama pull llama3.2:3b`. The model is stored in the named `ollama_data` volume for later runs.

**Windows file sharing or Docker Desktop errors**: make sure the repository directory is available to Docker Desktop under Settings > Resources > File Sharing.

**Ollama returns `provider_error`**: check `docker compose ps`, then run `docker compose exec ollama ollama list`. If `llama3.2:3b` is not listed, run `docker compose exec ollama ollama pull llama3.2:3b`. If the service is not running, restart with `docker compose up -d ollama` and retry.

**The browser shows an old frontend page**: stop the stack with `docker compose down`, rebuild with `docker compose up --build`, and refresh the browser with `Ctrl+F5`.

**PowerShell displays `>>`**: the previous command is incomplete. Press `Ctrl+C`, then paste the complete multi-line command again. Each continuation line must end with a PowerShell backtick `` ` ``.

**Need to inspect logs**:

```powershell
docker compose logs backend --tail 100
docker compose logs ollama --tail 100
docker compose logs frontend --tail 100
```

## Day 2 completion checklist

- [x] Docker Compose environment starts frontend, backend, PostgreSQL/pgvector, and Ollama.
- [x] Frontend shell renders at port 3000.
- [x] FastAPI `/health` endpoint works.
- [x] PostgreSQL connection and pgvector startup are verified.
- [x] Local Ollama model `llama3.2:3b` is downloaded and responds to the feasibility request.
- [x] API, AI, architecture, data, risk, backlog, and environment documents are included.
- [x] Secrets are excluded from Git through `.gitignore`.
- [x] MVP boundaries remain explicit: no direct court API, automatic filing, binding action, or lawyer replacement.

Day 2 is complete. Day 3 starts with case data models, authenticated case intake, document upload, extraction provenance, legal-source retrieval, and the first real dashboard workflow.

## Next implementation slices

1. Add organization, user, case, document, and case-event data models.
2. Add authenticated case intake and document upload endpoints.
3. Add document extraction with processing states and page-level provenance.
4. Add curated legal-source ingestion and pgvector retrieval.
5. Add structured assessment and human-review contracts.
