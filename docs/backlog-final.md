# Mawthooq Backlog — Day 1 to Day 6 (Closed)

**Team:** Mahmoud Ali, Ahmed Hatem, Aya Fawzy, Amr, Asiyah
**Submitted version:** `main @ 18ff5f1` (2026-09-13) — final commit, layering the Day 6 closing docs on top of the Day 5 feature commit `d3ff5e2` (2026-09-12)
**Reference:** `docs/backlog.md` (Day 3 working backlog, B1–B16) — this document closes it with Status and Evidence for every item, adds the Day 4–6 delivery rows, and records per-person contributions.
**Rule used throughout:** status is judged against code reality (`backend/app/routes.py`, `backend/app/database.py`, `ai/rag_sources.json`, `backend/tests/`, `frontend/src/`), not against design docs. `docs/api.md` describes several endpoints that were designed but never built — those are marked accordingly below.

---

## Day-by-day summary (by commit dates)

| Day | Date | Focus | Commits |
|---|---|---|---|
| Day 1 | 2026-09-08 | Project init, Docker Compose foundation (frontend/backend/PostgreSQL+pgvector/Ollama), health endpoints, docs skeleton | `978fb6f` |
| Day 2 | 2026-09-09 | AI providers (Ollama + Gemini) + `/ai/feasibility`, provider-free feasibility proof, case-management MVP (create/get/list), backlog ownership, README | `0601864`, `f017560`, `317a8a2`, `bb275fd`, `abe79e4`, `b85b3c8`, `03f7623` |
| Day 3 | 2026-09-10/11 | Secure document upload + processing states, page-level extraction with OCR fallback, embedding + chunking | `004a968` (part)* |
| Day 4 | 2026-09-11 | Legal-source RAG: 9→16 registry entries, provenance-preserving downloader + manifest, explicit ingestion CLI, jurisdiction/category-filtered cited search | `004a968`*, `4abc0d9` |
| Day 5 | 2026-09-12 | AI assessment + case chat (incl. SSE streaming), message history, DB pool + indexes + embedding cache, frontend intelligence section, API test suite | `d3ff5e2` |
| Day 6 | 2026-09-13 | Closing only (no features): demo video, final document, this backlog | `18ff5f1` + closing docs |

*Day 3 and Day 4 both cite `004a968` and overlap on the 2026-09-11 date because the extraction work (Day 3) and the start of the registry/RAG work (Day 4) landed in a single commit. They're kept as separate rows because they're distinct workstreams, not because the commit history is actually split that way — confirm against `git log` if this needs to be exact for the record.

---

## B1–B16 closed status

| ID | Task | Owner | Status | Evidence / note |
|---|---|---|---|---|
| B1 | SQLAlchemy/Alembic + org-scoped models | Amr | **Partial** | Persistence foundation exists but with raw psycopg DDL in `database.py:172-188`, not SQLAlchemy/Alembic; 9 tables built, but no Organization/User/Event tables. Org scoping deferred. |
| B2 | Authentication + org authorization | Amr | **Not done** | No auth middleware, tokens, or `organization_id` in `routes.py` / `database.py`; `api.md:40` itself states no authentication yet. |
| B3 | Case create/get endpoints (+ list bonus) | Amr | **Done** | `POST /api/cases`, `GET /api/cases/{id}`, plus `GET /api/cases` list (`routes.py:26-59`). Note: no update endpoint was built. |
| B4 | Secure upload + processing states | Amr + Mahmoud Ali | **Done** | Upload validation, private local storage, persisted metadata, observable statuses (`routes.py:62-73`). Correction: extraction is NOT still pending — see B5. |
| B5 | Text extraction + page provenance | Mahmoud Ali + Ahmed Hatem + Asiyah | **Done** | PDF/DOCX extraction, page numbers, language labels, quality states, AR/EN OCR fallback; `document_pages` table; `test_extraction.py`. |
| B6 | Curated legal-source fixture + pgvector retrieval | Mahmoud Ali + Ahmed Hatem + Asiyah | **Partial** | Retrieval pipeline itself is complete: ingestion CLI verifies manifest hashes, stores provenance + embeddings; `GET /api/legal-sources/search` filters by jurisdiction/category with `source-id:pN` citations. Corpus coverage is not complete: of the 16 registry entries (see D7), 7 are flagged `download:false` (blocked on publisher-confirmed URLs), leaving 9 eligible for ingestion — only 2 of those 9 have actually been downloaded and embedded (147 chunks). 7 eligible sources remain outstanding. |
| B7 | Structured assessment adapter + grounding | Mahmoud Ali + Ahmed Hatem + Asiyah | **Done** | `POST/GET /api/cases/{id}/assessments` persist schema-validated output; stream path strips ungrounded citations server-side; `requires_human_review` always true. |
| B8 | Dashboard + case-intake screens | Aya Fawzy | **Partial** | Intake form + created-case panel + backend-status indicator done (`main.jsx:169-206`); no multi-case dashboard page (single-page app). |
| B9 | Intelligence + verification screens | Aya Fawzy | **Partial** | Assessment (summary/risks/questions/citations + disclaimer) and streaming chat render (`main.jsx:215-251`); no journey/timeline or action-verification screens. |
| B10 | Assessment, verification, checklist, review endpoints | Amr + Mahmoud Ali + Ahmed Hatem + Asiyah | **Partial** | Assessment endpoints done (`routes.py:103-127`); action-verification, checklist, draft, and review endpoints from `api.md:268-289` were designed but NOT built. |
| B11 | Grounding + contract tests | Mahmoud Ali + Ahmed Hatem + Asiyah | **Partial** | 58/58 backend tests passing (10 files); no ≥90%-traceable-claims measurement report exists, so the metric is unproven. |
| B12 | UX copy + safety boundaries | Mahmoud Ali + Ahmed Hatem + Asiyah | **Done** | Disclaimer banner, no guarantee/replacement/filing language in UI, prompts, or docs. |
| B13 | OCR + bilingual extraction | Mahmoud Ali + Ahmed Hatem + Asiyah | **Partial** | Fallback + language columns shipped; no formal AR/EN evaluation artifact. |
| B14 | Draft filing preparation | Full team | **Not done** | No draft endpoint, table, or UI. Deferred (Should). |
| B15 | Notifications + portfolio view | Full team | **Out of scope** | Explicitly postponed. |
| B16 | Court integration / automatic filing | Full team | **Out of scope** | Requires separate product + legal approval; excluded by safety boundaries. |

---

## Day 4–6 delivery rows (work with no B-item)

| ID | Delivered | Owner | Status | Evidence |
|---|---|---|---|---|
| D1 | Document indexing endpoint (`POST /api/documents/{id}/index`) | Amr + Mahmoud Ali | Done | `routes.py:89-100`, `services.py` chunk+embed flow |
| D2 | Case-document search (`GET /api/search`) + blank-query guard | Mahmoud Ali + Ahmed Hatem + Asiyah | Done | `routes.py:184-193`; 400 without calling Ollama |
| D3 | Legal-search API test suite | Mahmoud Ali + Ahmed Hatem + Asiyah | Done | `test_legal_search_api.py` (success/empty/400/422/503 cases) |
| D4 | Assessment + chat + SSE streaming + message history | Mahmoud Ali + Ahmed Hatem + Asiyah | Done | `routes.py:103-182`; `stream_ollama_tokens`; `main.jsx:215-251` |
| D5 | Citation validation (stream path) | Mahmoud Ali + Ahmed Hatem + Asiyah | Done | `extract_citations` (`services.py`); invented citations dropped before storing |
| D6 | DB pool (1–10) + 8 b-tree indexes + embedding cache | Amr | Done | `database.py` pool/indexes; `rag.py` LRU-128; `test_database_opt.py` |
| D7 | Registry 9→16 entries (7 candidates `download:false`, Execution Law flip candidate) | Mahmoud Ali + Ahmed Hatem + Asiyah | Done | `ai/rag_sources.json`; blocked on publisher-confirmed PDF URLs. Registry metadata only — actual ingestion coverage is tracked separately under B6 (Partial). |
| D8 | Frontend intelligence section (assessment + streaming chat UI) | Aya Fawzy | Done | `main.jsx`, `api.js`, `styles.css` |
| D9 | Prompt trim (6 chunks × 500 chars), measured 49s→17s first token | Mahmoud Ali + Ahmed Hatem + Asiyah | Done | `ai_provider.py` `EVIDENCE_CHUNK_CHARS`; live-probe observation |
| D10 | Closing pack: demo video, final document, this backlog | Full team | Done | Submission folder 01–04 |

---

## Per-person contributions


- **Amr** — backend skeleton, case APIs (B1 partial, B3), upload + processing states (B4, with Mahmoud Ali), document indexing (D1, with Mahmoud Ali), DB pool/indexes (D6), assessment/verification/checklist/review endpoints (B10 partial, with Mahmoud Ali, Ahmed Hatem, Asiyah).
- **Aya Fawzy** — case-intake screens (B8 partial), intelligence + chat UI (B9 partial, D8).
- **Mahmoud Ali, Ahmed Hatem, Asiyah** — extraction/provenance (B5), upload + processing states (B4, with Amr), legal-source RAG pipeline and registry (B6 partial, D7), assessment/chat/streaming agents (B7, D4, D5, D9), case-document search (D2), document indexing (D1, with Amr), assessment/verification/checklist/review endpoints (B10 partial, with Amr), grounding/API tests (B11 partial, D3), safety copy (B12), OCR/bilingual extraction (B13 partial).
- **Full team** — contract reviews, closing pack (D10); B15/B16 explicitly out of scope.

## Deferred / not done (consolidated)

B2 (auth), B14 (drafts), B10-remainder (verification/checklist/review endpoints), B8/B9-remainder (dashboard, journey/timeline screens), B11-metric (90% grounding report), B1-remainder (SQLAlchemy/Alembic + org scoping), B6-remainder (7 of 9 eligible registry sources not yet downloaded/ingested).   
---

#