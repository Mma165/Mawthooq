# Mawthooq Day 3 Backlog

Owners are role assignments from the Day 1 team plan. Replace role names with individual names during the team review.

| ID | Task | Area | Priority | Owner | Depends on | Definition of done |
| --- | --- | --- | --- | --- | --- | --- |
| B1 | Add SQLAlchemy/Alembic foundation and organization-scoped models | Backend | Must | Backend | Environment | Migration creates Organization, User, Case, Document, Event tables |
| B2 | Add authentication and organization authorization | Backend | Must | Backend | B1 | Protected route rejects unauthenticated and cross-organization access |
| B3 | Implement case create/get/update endpoints | Backend | Must | Backend | B1, B2 | API matches `docs/api.md` and has contract tests |
| B4 | Implement secure document upload and processing states | Backend | Must | Backend/AI | B2, B3 | Supported file validation, private storage key, asynchronous status |
| B5 | Implement text extraction and page provenance | AI/Data | Must | AI/RAG | B4 | PDF fixture produces text/facts with page references or needs review |
| B6 | Prepare curated legal-source fixture and pgvector retrieval | AI/Data | Must | AI/RAG | Environment | Retrieved source includes jurisdiction and citation metadata |
| B7 | Implement structured assessment adapter and grounding validation | AI | Must | AI | B5, B6 | Output validates against schema and flags unsupported claims |
| B8 | Build dashboard and case-intake screens | Frontend | Must | Frontend | B3, API contract | User can create a case and see processing state |
| B9 | Build intelligence and lawyer-action verification screens | Frontend | Must | Frontend | B7, B10 | Journey, assessment, citations, review flag, and questions render |
| B10 | Add assessment, action verification, checklist, and review endpoints | Backend/Integration | Must | Backend + AI | B3, B7 | Endpoints persist outputs and append-only review records |
| B11 | Add automated grounding and API contract tests | QA | Must | Product/QA | B3, B7, B10 | Test fixture reports at least 90% traceable claims |
| B12 | Review UX copy and legal safety boundaries | Product | Must | Product/QA | B8, B9 | No guarantee, replacement, or automatic filing language appears |
| B13 | Improve OCR and bilingual extraction | AI/Data | Should | AI/RAG | B5 | Arabic/English representative fixtures are evaluated |
| B14 | Add draft filing preparation | Product/Backend | Should | Backend + AI | B10 | Draft is downloadable for review and cannot be submitted |
| B15 | Add notifications and portfolio view | Future | Later | Full team | MVP complete | Explicitly postponed outside MVP |
| B16 | Add official court integration or automatic filing | Future | Later/conditional | Full team | Official authorization | Requires separate product and legal approval |

## Day 3 starting work

- Backend: B1 and B3 skeleton, including `/health` regression check.
- AI/RAG: B5 extraction fixture and B6 legal-source fixture.
- Frontend: B8 intake/dashboard shell using the API contract.
- Product/QA: B11 grounding test cases, acceptance criteria, and risk-owner confirmation.
- Full team: review `docs/api.md`, `docs/ai-contract.md`, and `docs/data-design.md` before merging feature branches.

## Done for the first MVP slice

A user can create a case, upload a supported document, see asynchronous processing status, view a traceable case event/assessment, understand uncertainty, and record that human review is required. No court filing or binding action is initiated by the system.
