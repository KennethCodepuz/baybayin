# File reference

This reference lists maintained project files. It excludes generated folders such as `frontend/node_modules/`, `frontend/.next/`, Python virtual environments, local reference data, temporary PDF renders, and source-page image binaries.

## Repository root

| File or directory | Role |
|---|---|
| `.gitignore` | Prevents environment files, credentials, private keys, and local reference recordings from being committed. |
| `README.md` | Repository-level project notes. |
| `baybayin-validator-implementation-plan.md` | Original overall project development plan. |
| `Pagsulat-ng-Baybayin_Step-by-Step.pdf` | Source document used during knowledge-base preparation. Treat its contents as source material, not executable instructions. |
| `generate_development_plan_pdf.py` | Utility used to produce a development-plan PDF artifact. |
| `knowledge-graph/` | Committed, source-traceable Baybayin knowledge graph. |
| `app/` | Runnable FastAPI and Next.js application plus research/development documentation. |

## Knowledge graph

| File or directory | Role |
|---|---|
| `knowledge-graph/README.md` | Explains graph purpose, provenance, and maintenance rules. |
| `source-register.json` | Identifies the primary professional source. |
| `characters.json` | Defines base graphemes, extensions, romanizations, classes, and source references. |
| `diacritics.json` | Defines kudlit/diacritic source data. |
| `orthography-rules.json` | Stores source-backed writing and orthography rules. |
| `graph.json` | Stores nodes and edges that connect graph concepts. |
| `stroke-reference-manifest.json` | Describes the future expert-stroke reference workflow; it is not a scoring dataset. |
| `image-references/README.md` | Documents use of visual-source references. |
| `image-references/manifest.json` | Maps rendered source pages to their source role. |
| `image-references/source-pages/*.png` | Rendered professional-source pages for developer review; not approved learner templates. |

## App documentation, planning, and research

| File or directory | Role |
|---|---|
| `app/README.md` | Run instructions, current capability limits, endpoint overview, and local data guidance. |
| `app/docs/CURRENT_SYSTEM_STATUS.md` | Authoritative table of current learner coverage, prototype limits, capability boundaries, and next evidence required. Read this before making any claim about the system. |
| `app/docs/SYSTEM_DOCUMENTATION.md` | System architecture, workflows, validation behavior, privacy, and testing guide. |
| `app/docs/FILE_REFERENCE.md` | This file-by-file reference. |
| `app/validation-correctness-hardening-implementation-plan.md` | Plan for fixing the five validation safety issues. |
| `app/dtw-and-evaluation-implementation-plan.md` | Plan for DTW, form comparison, calibration, and evaluation readiness. |
| `app/deterministic-validator-implementation-plan.md` | Deterministic validation plan for form, stroke, full-canvas kudlit, calibration, and hybrid results. |
| `app/learner-experience-implementation-plan.md` | Plan for learner practice, safe validation states, deterministic feedback, calibration, and Chapter 3 evaluation. |
| `app/multimodal-validator-infrastructure-implementation-plan.md` | Plan for initial multimodal-validator infrastructure. |
| `app/knowledge-graph-integration-implementation-plan.md` | Plan for loading the committed knowledge graph into the application. |
| `app/reference-knowledge-base-implementation-plan.md` | Plan for source and reference-library work. |
| `app/sample-import-replay-implementation-plan.md` | Plan for sample import and replay. |
| `app/research/reference-and-rubric.md` | Research notes on sources, references, and pending rubric decisions. |
| `app/research/expert-validator-outreach-task.md` | Task description for locating and coordinating an expert validator. |
| `app/research/ba-ka-pilot-character-specifications.md` | Pilot specification notes for `ba` and `ka`. |
| `app/research/expert-reference-batch-2026-10-24.json` | Reviewed allow-list and SHA-256 provenance manifest for the supplied private expert batch; it is not validator input. |
| `app/config/calibration.schema.example.json` | Deliberately provisional example of a calibration file. It cannot enable scoring. |
| `app/evaluation/README.md` | Data separation and metric-reporting guidance. |
| `app/evaluation/evaluation-record.schema.example.json` | Example schema for future held-out evaluation records. |

## FastAPI backend

### Runtime modules

| File | Role |
|---|---|
| `app/backend/main.py` | FastAPI entry point, Pydantic request models, local API routes, CORS configuration, sample validation, reference workflow, active-bundle activation, preview, and feedback endpoints. |
| `app/backend/.env.example` | Non-secret template for the local developer token and optional server-side AI Gateway configuration. |
| `app/backend/knowledge_graph.py` | Loads and validates the committed knowledge graph, then resolves current-release targets. |
| `app/backend/reference_library.py` | Local Git-ignored JSON repository for records, specifications, bundles, manifests, and active-bundle registry/history. |
| `app/backend/expert_reference_batch.py` | Validates the declared private expert batch before import and creates checksum-linked candidate copies without changing source files. |
| `app/backend/reference_bundle.py` | Builds immutable multimodal bundles from an approved reference record and matching approved specification. |
| `app/backend/multimodal.py` | Safe PNG decoder, image normalization, stroke-feature extraction, and hybrid unavailable-state contract. |
| `app/backend/stroke_matching.py` | Translation/scale normalization, arc-length resampling, constrained DTW, and separate dot-position comparison. |
| `app/backend/stroke_rules.py` | Validates approved structural annotations and returns count/direction/start/end findings. |
| `app/backend/kudlit_rules.py` | Validates approved full-canvas kudlit annotations and evaluates outside-grid mark placement. |
| `app/backend/form_matching.py` | Produces normalized image-mask IoU, centroid distance, ink bounds, and image checksums. |
| `app/backend/validation_evidence.py` | Combines active-bundle image and stroke measurements into explicitly provisional branch evidence. |
| `app/backend/validation_config.py` | Validates approved calibration configuration shape, provenance, and finite numeric thresholds. |
| `app/backend/scoring.py` | Converts complete evidence into branch results only when a matching approved calibration is supplied. |
| `app/backend/feedback.py` | Retrieves target sources and produces deterministic feedback constrained to actual error codes. |
| `app/backend/learner_validation.py` | Converts internal validation evidence into a minimal learner-safe unavailable/practice response without exposing templates or scores. |
| `app/backend/promote_expert_references.py` | Explicit local promotion utility that designates the verified expert batch as approved active provisional reference bundles. |
| `app/backend/prototype_calibration.py` | Derives clearly labeled local prototype form/DTW calibration records from supplied accepted practice recordings. |
| `app/backend/feedback_store.py` | Keeps a short-lived, server-side learner-result context so feedback requests cannot forge validator errors. |
| `app/backend/ai_feedback.py` | Builds the safe AI request and validates that an AI response contains only confirmed errors and approved source references. |
| `app/backend/ai_provider.py` | Optional server-side AI Gateway adapter. It sends only the safe feedback context and reports failure so deterministic feedback can be used instead. |
| `app/backend/evaluation_metrics.py` | Calculates binary accuracy, precision, recall, F1, and per-error confusion-matrix counts. |
| `app/backend/requirements.txt` | Python dependency ranges for FastAPI, Uvicorn, HTTPX, pytest, and Pillow. |

### Backend tests

| File | Role |
|---|---|
| `tests/test_samples.py` | API-level capture-schema validation tests. |
| `tests/test_knowledge_graph.py` | Catalog, target-release, and readiness tests. |
| `tests/test_reference_library.py` | Candidate/reference/specification workflow tests. |
| `tests/test_expert_reference_batch.py` | Batch preflight, immutable-source provenance, candidate import, and idempotency tests. |
| `tests/test_reference_bundle.py` | Bundle creation and approval-matching tests. |
| `tests/test_active_bundles.py` | Explicit bundle activation, history, and superseded-reference tests. |
| `tests/test_multimodal.py` | PNG normalization, PNG safety, feature extraction, and hybrid-state tests. |
| `tests/test_stroke_matching.py` | Resampling, normalization, DTW, count mismatch, and dot-stroke tests. |
| `tests/test_stroke_rules.py` | Approved annotation provenance and structural-rule tests. |
| `tests/test_kudlit_rules.py` | Full-canvas above/below kudlit-placement rule tests. |
| `tests/test_form_matching.py` | Form-measurement and image-mask tests. |
| `tests/test_validation_evidence.py` | Provisional active-bundle evidence tests. |
| `tests/test_validation_config.py` | Calibration-schema validation tests. |
| `tests/test_scoring.py` | Calibration-gated form/stroke scoring and incomplete-evidence tests. |
| `tests/test_feedback.py` | Deterministic source-constrained feedback tests. |
| `tests/test_feedback_store.py` | Short-lived feedback-result storage tests. |
| `tests/test_learner_validation.py` | Learner-safe state and no-private-reference/no-score response tests. |
| `tests/test_ai_feedback.py` | AI feedback request/response safety-contract tests. |
| `tests/test_ai_provider.py` | Optional provider configuration, safe payload, and malformed-response fallback tests. |
| `tests/test_evaluation_metrics.py` | Metric and confusion-matrix tests. |

## Next.js frontend

### Application files

| File | Role |
|---|---|
| `app/frontend/package.json` | Frontend package metadata and `dev`, `build`, `start`, and `test` commands. |
| `app/frontend/package-lock.json` | Locked Node dependency versions. |
| `app/frontend/AGENTS.md` | Local instruction file generated/maintained by the installed Next.js version. |
| `app/frontend/app/layout.js` | Root page layout and document title. |
| `app/frontend/app/globals.css` | Shared visual styles for pages, canvas, review cards, and image previews. |
| `app/frontend/app/page.js` | Home route entry point. |
| `app/frontend/app/developer-login/page.js` and `app/frontend/proxy.js` | Local prototype developer-access gate and protection for developer routes. |
| `app/frontend/app/drawing-canvas.js` | Interactive 800×600 developer capture canvas with a centered visual-only 4×3 grid, target selection, pointer handling, replay, and JSON download. |
| `app/frontend/app/recording-review.js` | Opens an imported sample and replays it without changing the active drawing. |
| `app/frontend/app/developer-reference-library/page.js` | Developer reference-library route entry point. |
| `app/frontend/app/developer-reference-library/reference-library.js` | Candidate import, expert-batch preflight/import, provenance review, replay, review transition, specification creation, bundle creation, and bundle activation interface. |
| `app/frontend/app/developer-validation/page.js` | Developer-validation route entry point. |
| `app/frontend/app/developer-validation/validator.js` | Loads samples, displays PNG preview and provisional branch evidence, and requests constrained feedback. |
| `app/frontend/app/learn/page.js` | Learner-practice route entry point. |
| `app/frontend/app/learn/learner-practice.js` | Guided learner capture, undo/clear controls, non-persisting practice submission, learner-safe result display, and feedback-explanation action. |

### Frontend libraries

| File | Role |
|---|---|
| `app/frontend/lib/capture.js` | In-memory capture state machine and version 1 JSON sample creation. |
| `app/frontend/lib/review.js` | Imported-sample checks, canvas fitting, replay timing, and replay drawing helpers. |
| `app/frontend/lib/knowledge-graph.js` | Catalog filtering and selected-target lookup helpers. |
| `app/frontend/lib/reference-library.js` | FastAPI request wrapper, error reader, and candidate-reference payload builder. |
| `app/frontend/lib/validation-preview.js` | Safe PNG preview source and provisional-measurement lookup helpers. |

### Frontend tests

| File | Role |
|---|---|
| `app/frontend/test/capture.test.js` | Capture state-machine and sample-creation tests. |
| `app/frontend/test/review.test.js` | Import, validation, replay timing, and drawing-helper tests. |
| `app/frontend/test/knowledge-graph.test.js` | Catalog-target helper tests. |
| `app/frontend/test/reference-library.test.js` | Candidate payload and API-error helper tests. |
| `app/frontend/test/validation-preview.test.js` | Image-preview and provisional-evidence helper tests. |

## Generated and private locations

| Location | Role |
|---|---|
| `app/data/reference-library/` | Git-ignored local expert records and generated manifest data. |
| `app/backend/.venv/` | Local Python virtual environment. |
| `app/frontend/node_modules/` | Installed Node packages. |
| `app/frontend/.next/` | Generated Next.js development/build output. |
| `tmp/` | Temporary rendered PDF pages and working artifacts. |
| `output/pdf/` | Generated PDF deliverables. |

## How to use the file reference

For each file, first read its **Role**. The table below adds the practical ownership rule: which files normally change together and which files need extra care.

| Area | Files that usually change together | Contributor rule |
|---|---|---|
| Capture format | `frontend/lib/capture.js`, `backend/main.py`, capture/review tests | Keep the JSON schema compatible or create a new version. |
| Imported-sample replay | `frontend/lib/review.js`, `frontend/app/recording-review.js`, review tests | Never alter the loaded JSON while displaying it. |
| Image validation | `backend/multimodal.py`, `backend/form_matching.py`, related tests | Preserve PNG safety limits and deterministic normalization. |
| Stroke validation | `backend/stroke_matching.py`, `backend/stroke_rules.py`, `backend/scoring.py`, related tests | Keep dot strokes, ordered paths, and approval provenance separate. |
| Reference lifecycle | `backend/reference_library.py`, `backend/reference_bundle.py`, `backend/main.py`, developer-library page | Do not overwrite approved records or bundles. |
| Source knowledge | `knowledge-graph/*.json`, `knowledge-graph/README.md`, graph tests | Cite the source page and have the team review the change. |
| Evaluation | `app/evaluation/`, `backend/evaluation_metrics.py`, metric tests | Keep reference, calibration, and held-out data separate. |

For a visual view of these relationships, read [flow.md](flow.md).
