# Mawthooq Risk Register

| Risk | Impact | Owner | Fallback / mitigation | Day 2 status |
| --- | --- | --- | --- | --- |
| Legal sources are incomplete, outdated, or wrong jurisdiction | Unsupported guidance | AI/RAG | Curated approved sources, jurisdiction/date filters, no-source means no conclusion | Open |
| LLM hallucinates or misses citations | Unsafe case understanding | AI | Structured output, citation validation, claim grounding metric, human review | Open |
| Scanned or Arabic/English documents extract poorly | Wrong facts or dates | AI/Data | PyMuPDF first, OCR fallback, extraction quality score, manual review | Open |
| Uploaded document contains prompt injection | Model follows document instructions | Backend/AI | Treat uploads as untrusted evidence, isolate prompts, allowlist tools, no automatic actions | Open |
| Confidential case data crosses tenant boundary | Privacy breach | Backend | Organization-scoped queries, authorization tests, private object storage, audit logs | Open |
| Model API quota, cost, or availability | Delayed analysis | Backend/AI | Provider adapter, timeout/retry, deterministic fixture, preserve existing case data | Open |
| Confidence is not calibrated | Users over-trust output | Product/QA | Evidence-based confidence basis, evaluation set, always expose assumptions and uncertainty | Open |
| Human review is only a visual warning | Unsafe final decisions | Product/Backend | Persist reviewer, decision, timestamp, evidence reviewed, and changed assumptions | Open |
| Team lacks a shared contract | Integration delays | Full team | Versioned API/AI/data docs, feature branches, pull-request review | Managed |
| No official court API is available | Scope confusion | Product | MVP uses user-uploaded notices; court integration remains conditional future work | Managed |
