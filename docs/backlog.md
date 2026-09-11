# Mawthooq Day 3 Backlog

Ownership is assigned to the five Mawthooq team members: Mahmoud Ali, Ahmed Hatem, Aya Hegazy, Amr, and Asiyah. Shared tasks require collaboration from the full team.

| ID | Task | Area | Priority | Owner | Depends on | Definition of done |
| --- | --- | --- | --- | --- | --- | --- |
| B1 | Add SQLAlchemy/Alembic foundation and organization-scoped models | Backend | Must | Amr | Environment | Migration creates Organization, User, Case, Document, Event tables |
| B2 | Add authentication and organization authorization | Backend | Must | Amr | B1 | Protected route rejects unauthenticated and cross-organization access |
| B3 | Implement case create/get/update endpoints | Backend | Must | Amr | B1, B2 | API matches `docs/api.md` and has contract tests |
| B4 | Implement secure document upload and processing states | Backend/AI | Must | Amr + Mahmoud Ali | B2, B3 | **Integrated Day 4:** supported file validation, private local storage key, persisted metadata, and observable `uploaded` status. Extraction remains pending. |
| B5 | Implement text extraction and page provenance | AI/Data | Must | Mahmoud Ali + Ahmed Hatem + Asiyah | B4 | **Gate 1 complete:** PDF/DOCX extraction, page references, language labels, quality states, and Arabic/English OCR fallback |
| B6 | Prepare curated legal-source fixture and pgvector retrieval | AI/Data | Must | Mahmoud Ali + Ahmed Hatem + Asiyah | Environment | **Implemented:** explicit approved-PDF ingestion, manifest verification, pgvector chunks, and jurisdiction/category-filtered cited retrieval. |
| B7 | Implement structured assessment adapter and grounding validation | AI | Must | Mahmoud Ali + Ahmed Hatem + Asiyah | B5, B6 | Output validates against schema and flags unsupported claims |
| B8 | Build dashboard and case-intake screens | Frontend | Must | Aya Hegazy | B3, API contract | User can create a case and see processing state |
| B9 | Build intelligence and lawyer-action verification screens | Frontend | Must | Aya Hegazy | B7, B10 | Journey, assessment, citations, review flag, and questions render |
| B10 | Add assessment, action verification, checklist, and review endpoints | Backend/AI Integration | Must | Amr + Mahmoud Ali + Ahmed Hatem + Asiyah | B3, B7 | Endpoints persist outputs and append-only review records |
| B11 | Add automated grounding and API contract tests | QA/AI | Must | Mahmoud Ali + Ahmed Hatem + Asiyah | B3, B7, B10 | Test fixture reports at least 90% traceable claims |
| B12 | Review UX copy and legal safety boundaries | Product/AI | Must | Mahmoud Ali + Ahmed Hatem + Asiyah | B8, B9 | No guarantee, replacement, or automatic filing language appears |
| B13 | Improve OCR and bilingual extraction | AI/Data | Should | Mahmoud Ali + Ahmed Hatem + Asiyah | B5 | Arabic/English representative fixtures are evaluated |
| B14 | Add draft filing preparation | Product/Backend/AI | Should | Amr + Mahmoud Ali + Ahmed Hatem + Asiyah | B10 | Draft is downloadable for review and cannot be submitted |
| B15 | Add notifications and portfolio view | Future | Later | Full team | MVP complete | Explicitly postponed outside MVP |
| B16 | Add official court integration or automatic filing | Future | Later/conditional | Full team | Official authorization | Requires separate product and legal approval |

## Day 3 starting work

- Amr: B1 and B3 backend skeleton, including `/health` regression check.
- Aya Hegazy: B8 dashboard and case-intake shell using the API contract.
- Mahmoud Ali, Ahmed Hatem, and Asiyah: B5 and B6 extraction, legal-source retrieval, and AI feasibility work.
- Mahmoud Ali, Ahmed Hatem, and Asiyah: B7 structured AI assessment and grounding tests.
- Full team: review `docs/api.md`, `docs/ai-contract.md`, and `docs/data-design.md` before merging feature branches.

## Done for the first MVP slice

A user can create a case, upload a supported document, and see its persisted `uploaded` processing status. Text extraction, traceable case events, assessments, authentication, and human review workflows remain pending. No court filing or binding action is initiated by the system.
