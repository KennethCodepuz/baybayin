# Implementation plan: developer reference library and knowledge-base foundation

**Status:** Proposed plan; no feature implementation is included in this document.  
**Goal:** Let developers curate approved expert drawing recordings for a small `ba` and `ka` pilot, preserve their provenance, and create a source-traceable foundation for the future validator and knowledge graph.  
**Approach:** Test-driven development. Write each test before the corresponding implementation, confirm it fails for the intended reason, make the smallest change, then rerun the relevant test suite.

## 1. Scope and current state

The app can capture a drawing, export version 1 JSON, reopen an exported file, and replay its event sequence. FastAPI currently checks capture structure only and does not persist files or judge Baybayin correctness. The supplied PDF provides visual references for `ba` and `ka`, but the meaning of its numbered marks, accepted forms, stroke order, direction, and pen lifts remain pending expert review.

This phase creates a **developer-only reference library**. It will accept a selected sample only after it has been structurally checked, attach review metadata, and keep a manifest of records that can later feed a knowledge graph. It will not tell learners whether their writing is correct.

The initial pilot is deliberately limited to unmodified `ba` and `ka`. A recording is a candidate reference until its metadata says it is approved by a qualified reviewer. No unreviewed sample, generated fixture, or PDF observation becomes validator ground truth.

## 2. Deliverables

1. A versioned metadata schema for reference records and character specifications.
2. A developer-only reference-library screen for importing, inspecting, and assigning review status to local sample files.
3. A FastAPI persistence API that stores validated samples and their metadata in a local development data directory.
4. A manifest export suitable for later graph ingestion, with stable identifiers and links among records, character specifications, source pages, and reviewer decisions.
5. Fixtures and automated tests that distinguish approved reference data from test data.
6. Documentation for the expert-review and reference-recording workflow.

## 3. Data model decisions

### Reference record

Each stored reference record should contain:

- `id`: generated stable identifier;
- `sample`: the unchanged version 1 capture payload, including ordered events and final image;
- `target`: copied from the checked sample and restricted in this pilot to `ba` or `ka`;
- `status`: `candidate`, `approved`, `rejected`, or `superseded`;
- `specificationVersion`: the reviewed rule-set version the record supports, initially unset;
- `source`: title, page reference, and convention identifier;
- `review`: reviewer identifier or role, review date, decision, and notes;
- `capture`: device or input method when known, and original creation time;
- `provenance`: import time, application schema version, and a checksum of the raw sample;
- `supersedes`: optional reference-record ID;
- `dataClass`: `reference` or `test`.

Store reviewer display names only when the research team has approved doing so. Prefer a stable reviewer code in the manifest. Do not put a participant name in the drawing target or the sample itself.

### Character specification

The system needs a separate versioned record for each character, rather than embedding rules in individual JSON samples. A pilot specification should identify the target, convention, source pages, allowed forms, approved stroke formations, excluded variants, unresolved questions, reviewer decision, and approval date.

Before expert review, all rule fields remain `pending`. The developer library can link a candidate sample to a draft specification, but the API must reject an attempt to mark it `approved` until the linked specification has an approval decision and version.

### Storage and manifest

For this pilot, use a project-local, git-ignored development data directory such as `app/data/reference-library/`. Keep each original sample as its own JSON file and maintain a separate manifest JSON file. The manifest is the graph-ready index; samples remain evidence files.

Do not commit collected recordings, reviewer notes, manifests containing non-public information, or local credentials. Commit only synthetic fixtures with `dataClass: test` and documentation that explains the expected structure. The future deployed system will need authenticated storage and a team-approved retention policy; that is outside this local development phase.

## 4. Developer workflow

1. A developer starts the local Next.js and FastAPI services and opens the protected developer route.
2. They select a downloaded drawing JSON. The browser and backend check the existing version 1 capture structure.
3. The developer sees the replay, final image, target, capture details, checksum, and an explicit **candidate reference** status.
4. They enter permitted metadata: target, source page, convention, input method, specification link, and review decision. The interface never offers `approved` unless the specification has been approved.
5. The backend creates an ID, saves the original sample plus metadata, and adds a manifest entry. It returns the saved record for display.
6. Developers can list, filter, open, replay, supersede, or mark a record rejected. Status changes preserve the previous record and its provenance.
7. A developer exports the manifest for later knowledge-graph work. The export contains references and decisions, not an assertion that any PDF diagram alone defines a stroke rule.

## 5. TDD implementation sequence

### Step 1 - Define schemas and fixtures

1. Write backend tests for valid and invalid reference-record metadata, valid statuses, target restrictions, required provenance, and immutable original samples.
2. Add synthetic fixtures for `ba`, `ka`, malformed samples, and a test-only approved specification. Label every fixture as test data.
3. Implement Pydantic models and a schema-version field only after the tests fail.

**Done when:** The API accepts a complete candidate record, rejects invalid metadata, and cannot mistake test fixtures for approved reference records.

### Step 2 - Implement local repository and persistence API

1. Write tests using a temporary data directory for record creation, retrieval, listing, duplicate detection by checksum, and manifest generation.
2. Implement a repository layer that writes each record atomically and updates the manifest safely.
3. Add API endpoints for creating, listing, retrieving, and exporting records. Return clear conflicts for duplicate imports and clear validation errors for unsupported data.
4. Add the local data directory and any generated manifest to the top-level `.gitignore`.

**Done when:** The API can store and retrieve a checked candidate without changing its original sample, and the repository data does not appear in `git status`.

### Step 3 - Gate approval with reviewed specifications

1. Write tests showing that a candidate cannot become approved with a missing, draft, or mismatched specification version.
2. Implement specification storage and the allowed status transitions: `candidate -> approved`, `candidate -> rejected`, and `approved -> superseded` only with the required decision metadata.
3. Record every transition with its date, reviewer code, reason, and relevant source-page reference.

**Done when:** Only an approved specification can support an approved recording, and the manifest exposes the link between them.

### Step 4 - Build the developer library interface

1. Write frontend tests for empty, loading, import-success, duplicate, validation-failure, and API-unavailable states.
2. Write tests for filtering by target and status, replaying a stored record, and displaying source and review provenance as text.
3. Implement a clearly labelled developer route and import form. Reuse the existing replay component where possible, while keeping the capture screen separate.
4. Implement a record detail view with controlled status actions. Require the necessary metadata in the form before sending a transition request.

**Done when:** A developer can create and inspect a candidate record, while the interface makes clear that it is not learner validation.

### Step 5 - Export graph-ready manifest and document the workflow

1. Write tests for deterministic manifest output, stable IDs, source/specification links, and exclusion of rejected or test records from the default reference export.
2. Implement a JSON manifest export with records, character specifications, source references, and graph relationships such as `represents`, `reviewedAgainst`, `supports`, and `supersedes`.
3. Update the README with developer startup, data location, backup/export procedure, and the distinction between candidate and approved references.
4. Update the expert outreach material with the handoff procedure once a reviewer is confirmed.

**Done when:** The team can hand an exported manifest and its linked reference recordings to the later validator or graph-development phase with enough provenance to audit each item.

### Step 6 - Verify the complete workflow

1. Run frontend and backend tests, plus the Next.js production build.
2. In a real browser, import a valid `ba` candidate, save it, list it, replay it, and export the manifest.
3. Verify that malformed samples, duplicate imports, an approval attempt without an approved specification, and a backend outage preserve existing library records.
4. Confirm the local data directory is ignored by Git and that no real expert recordings or private reviewer details appear in tracked files.

**Done when:** The developer-only reference flow works from capture JSON to audited local library and manifest export.

## 6. Acceptance criteria

- Only version 1 samples that pass structural checks can enter the reference library.
- Every record retains its original sample and has a stable ID, checksum, data class, and provenance.
- Candidate, approved, rejected, and superseded states are explicit and auditable.
- A sample cannot be approved without a matching expert-approved character specification.
- The library supports `ba` and `ka` without claiming either character's rules are final before review.
- Test fixtures remain distinct from expert reference data and are excluded from default graph exports.
- Recordings and private review metadata are stored only in git-ignored local data during this phase.
- Tests are written before implementation, all relevant checks pass, and the browser workflow is verified end to end.

## 7. Dependencies and blockers

Development can begin immediately for schemas, local storage, developer screens, fixtures, replay, and manifest export. The following work must wait for the expert review:

- marking any recording as approved ground truth;
- defining stroke-count, order, direction, and pen-lift rules;
- creating validator thresholds or correctness feedback;
- deciding accepted handwriting variations and kudlit handling.

The outreach task is in [expert-validator-outreach-task.md](research/expert-validator-outreach-task.md). When an expert is confirmed, use the reviewed `ba` and `ka` specification to seed the first approved reference set before starting stroke-validation logic.
