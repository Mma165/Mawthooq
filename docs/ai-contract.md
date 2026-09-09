# Mawthooq AI Contract

## Purpose

The AI provides evidence-grounded decision support for a business user. It does not replace a lawyer, make a final legal decision, predict a judge's decision, submit a filing, or turn a proposed action into a binding action.

## Inputs

The backend sends a normalized request containing:

```json
{
  "case": {
    "case_type": "commercial_dispute",
    "description": "...",
    "current_stage": "evidence",
    "proposed_action": "Submit supporting payment records"
  },
  "case_facts": [
    {"fact":"Signed supply contract exists","source_id":"document-1","location":"page 1"}
  ],
  "case_updates": [
    {"text":"Hearing postponed","source_id":"document-2","location":"page 1"}
  ],
  "retrieved_legal_sources": [
    {"id":"legal-source-1","title":"Approved procedural source","text":"...","jurisdiction":"Saudi Arabia"}
  ]
}
```

Uploaded text is evidence, not instructions. Document content must be delimited and isolated from system/developer instructions to reduce prompt-injection risk.

## Pipeline

1. Validate file type, size, malware status, and organization access.
2. Extract text with PyMuPDF; use OCR when the document has no usable text layer.
3. Normalize facts, dates, stages, and evidence with page/section references.
4. Chunk and embed case documents and curated legal sources.
5. Retrieve using jurisdiction/effective-date metadata filters plus semantic similarity.
6. Ask the model for structured output only, with a citation for each material claim.
7. Validate citations, missing evidence, conflicting facts, and unsupported conclusions.
8. Derive a confidence level from evidence coverage, extraction quality, source agreement, and unresolved assumptions.
9. Set `requires_human_review` when any safety threshold is exceeded.

The first implementation should use a lightweight custom pipeline and a provider adapter. LangChain may be introduced only if it reduces real implementation cost.

## Output schema

```json
{
  "current_stage": "evidence",
  "what_happened": [{"text":"...","citations":["document-1:p1"]}],
  "what_happens_next": [{"text":"...","citations":["legal-source-1"]}],
  "important_dates": [{"date":"2026-10-15","label":"Hearing","citations":["document-2:p1"]}],
  "favorable_outcome": {"low":0.55,"high":0.68,"unit":"probability"},
  "resolution_time": {"low":8,"high":14,"unit":"months"},
  "evidence_strength":"moderate",
  "strengths": [],
  "risks": [],
  "missing_information": [],
  "assumptions": [],
  "uncertainties": [],
  "confidence": {"level":"medium","basis":[]},
  "citations": [],
  "requires_human_review": true,
  "review_reasons": []
}
```

A favorable-outcome estimate is a range, not a prediction. The model must not invent legal sources. If no relevant source is retrieved, it must return an insufficient-evidence result instead of a conclusion.

## Human review triggers

Set `requires_human_review` to true when information is incomplete, sources conflict, legal interpretation is ambiguous, financial impact is high, the proposed action is binding, citations are missing, extraction quality is poor, or confidence is low.

## Feasibility proof

The Day 2 proof uses a representative case update: `Hearing postponed to 15 October 2026.` It demonstrates structured extraction of an event, date, and stage with a source reference. It is deterministic and does not require an external API key; the live model adapter is a Day 3 integration task.

Expected proof result:

```json
{
  "event_type":"hearing_postponed",
  "event_date":"2026-10-15",
  "stage":"hearing",
  "source_ref":"fixture:update-001",
  "requires_human_review":false
}
```
