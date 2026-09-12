# Mawthooq — Final Document

**Project:** Mawthooq — AI-powered legal case intelligence for businesses (Saudi Arabia)
**Submitted version:** `main @ d3ff5e2` ("adding the chat bot", 2026-09-12), working tree clean
**Team:** Mahmoud Ali, Ahmed Hatem, Aya Hegazy, Amr, Asiyah (ownership per `docs/backlog.md`)

---

## 1. Executive summary

Mawthooq helps a business decision-maker answer four questions about any legal dispute: **what is happening in my case, what comes next, why is an action recommended, and what must I verify with my lawyer?**

It does this by combining three things: (1) a structured case record with uploaded evidence documents, (2) a curated retrieval corpus of official Saudi legal sources (Arabic originals, page-cited), and (3) an AI agent that produces a grounded case assessment plus an interactive chat — always flagged as decision support requiring human lawyer review, never as legal advice, a court prediction, or a filing.

What was delivered is a **working single-page prototype**: case intake, evidence upload, Saudi legal-source search, AI assessment generation, and streaming case chat — backed by PostgreSQL + pgvector, an explicit approved-PDF ingestion pipeline, 58 passing backend tests, and a recorded demo.

---

## 2. Problem statement

Businesses involved in disputes (unpaid contracts, commercial conflicts, debts, employment matters) face the same pain:

- Case facts live in scattered PDFs, messages, and court notices — nobody maintains one case record.
- Owners cannot tell what stage a case is in or what the next procedural step is.
- When a lawyer proposes an action ("file an appeal", "submit payment records"), the owner has no independent way to check its basis or required evidence.
- Generic AI answers are ungrounded: no citations, no Saudi jurisdiction, no distinction between guidance and binding law — creating real risk of over-trust.

The cost of these gaps is missed deadlines, weak evidence files, and decisions made without understanding the procedural basis.

---

## 3. Target users and value proposition

**Primary user:** a business owner or manager in Saudi Arabia dealing with a commercial, contract, debt, or employment dispute, working *with* (not instead of) their lawyer.

**Value proposition:**
- One case record: facts, stage, proposed actions, and evidence documents in one place.
- Grounded answers: every material claim points to an official Saudi source page or an uploaded document page.
- Lawyer leverage: structured questions to ask counsel and a checklist mindset before approving any action.
- Safety by design: the system refuses to predict judges, submit filings, or present estimates as guarantees.

---

## 4. Methodology and approach

- **Incremental slices, main kept stable:** environment foundation → case management → document upload/extraction → legal-source RAG → assessment/chat agents → performance hardening. Feature branches merged into `main` (Sept 8–12).
- **Contract-first:** REST, AI, architecture, and data contracts were written before/with implementation (`docs/api.md`, `docs/ai-contract.md`, `docs/architecture.md`, `docs/data-design.md`).
- **Approved-source discipline:** only explicitly approved, hash-verified PDFs enter the corpus; ingestion is an explicit CLI command, idempotent by SHA-256; downloading is a separate explicit step.
- **Arabic-first RAG:** Arabic originals are the authority; retrieval is multilingual so Arabic and English questions retrieve Arabic sources.
- **Evidence before claims:** every feature was verified live against the Docker stack (health checks, ingestion runs, endpoint responses, streaming probes) and covered by backend tests.

---

## 5. Solution overview

**Running system (4 containers):** React/Vite frontend (:3000), FastAPI backend (:8000), PostgreSQL 16 + pgvector (:5432), Ollama (:11434) with `nomic-embed-text` embeddings and `llama3.2:3b` generation (Gemini optional).

**User journey (single page, 3 sections):**
1. **01 / Case intake** — case type (commercial dispute, employment, contract, debt, other), current stage (complaint → appeal), description, optional proposed lawyer action. Invalid input is rejected with clear errors.
2. **02 / Evidence** — attach PDF, DOCX, or image (10 MiB limit); page-level text extraction with language labels and quality states; documents are chunked, embedded, and indexed for case-scoped search.
3. **03 / AI intelligence** — one click generates a legal assessment (summary, what-happens-next with citations, risks, questions for the lawyer), then a chat box answers follow-up questions with **streaming replies** (words appear as generated) and validated citations.

**Corpus:** 16 approved registry entries; 2 PDFs downloaded and ingested (Consumer Rights Guide — 66 chunks; ZATCA dispute policies — 81 chunks). 7 further candidates (Labor Law, Commercial Court Law, Companies Law, Civil Procedures, Commercial Data rules, SAMA finance rules, MHRSD guides) are registered as `download: false` pending publisher-confirmed direct PDF URLs — which is why debt and employment retrieval is still uncovered.

**Engineering underneath:** 9 database tables, pooled DB connections (1–10), 8 b-tree indexes, embedding cache, validated-citation pipeline (invented citations are dropped before storing), and a documented decision *not* to add a pgvector HNSW index (dimensionless columns + 147-row corpus where sequential scan is optimal).

---

## 6. Safety boundaries (non-negotiable)

- Decision support only; `requires_human_review: true` on every AI output, with a visible disclaimer banner.
- No binding legal advice, no judge/outcome prediction, no filings, no court integration.
- Retrieval returns cited passages; the model may not invent sources — ungrounded citations are stripped server-side.
- Uploaded documents are evidence, never trusted instructions.

---

## 7. Delivered vs deferred

**Delivered and demoed:** environment, case intake, document upload/extraction/indexing, case-document search, Saudi legal-source ingestion + filtered cited search, AI assessment generation + listing, interactive streaming case chat + message history, feasibility proof endpoint, 58 passing tests.

**Deferred (no new work promised):** authentication/organization access, case updates/timeline, lawyer action-verification, checklists, review-only drafts, human-review records, multi-case dashboard, notifications, court integration. Note: `docs/api.md` describes some of these as if built — they are **designed, not implemented**; the code is the source of truth.

---

## 8. Measured results and evidence

Honest, verifiable figures only:

- Corpus: 2 PDFs ingested, 147 chunks with page provenance and embeddings.
- Tests: 58/58 backend tests passing (10 test files: schemas, uploads, extraction, chunking, ingestion, legal search, legal search API, assessments, streaming chat, DB optimization).
- Live verification: assessment generation returns `201` with grounded citations; chat streams `user → deltas → done` server-sent events with validated citations; health and database checks return `ok`.
- Observed generation speed (live probes, CPU-only inference, same question): streaming first token 49s → 17s and full reply 76s → 44s after evidence trimming (6 chunks × 500 chars). Remaining latency is CPU token generation (~7–12 tokens/sec), not database work — a faster model, API model, or GPU is the path below ~5s, deliberately left as a decision, not done here.
- Known limits stated openly: debt/employment queries return no legal sources until their PDFs are confirmed and ingested; the small local model occasionally phrases citations loosely (mitigated by server-side validation + human-review flag).

---

## 9. Risks carried forward

Per `docs/risk-register.md`: incomplete/outdated/wrong-jurisdiction sources (open — reduced by curation, increased in maintenance load per added source); model hallucination (mitigated by grounding + validation + review flag); over-trust by users (mitigated by disclaimers, but a UX/process risk, not a solved problem); personal-data retention for uploaded case documents (needs a retention decision before real customer data); no court API assumed — case context stays user-uploaded.

---

## 10. Team

Ownership per `docs/backlog.md`: extraction, legal-source retrieval, and AI work — Mahmoud Ali, Ahmed Hatem, Asiyah; backend skeleton and case APIs — Amr; dashboard/intake shell — Aya Hegazy; shared review — full team. Note on traceability: git history does not resolve per-person delivery beyond these assignments, so contributions above are stated at team level.

---

## 11. Pointers

- **Demo video:** see `01-Demo-Video/` in the submission folder.
- **Repository:** branch `main`, commit `d3ff5e2`, clean tree. Build and run: `docker compose up --build` (see README setup). Note: `data/` (PDFs, manifest), `.env`, and `uploads/` are git-ignored by design; corpus evidence travels as a manifest copy in the folder.
- **Backlog:** see `04-Updated-Backlog/` for the closed status of every item with code evidence.
