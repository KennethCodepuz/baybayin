# Implementation plan: security and correctness hardening

**Status:** Proposed; this document makes no runtime code changes.  
**Goal:** Close the security, privacy, reliability, and logic gaps found in the 23 October 2026 audit while keeping the application a local developer and expert-reference tool.  
**Method:** Test-driven development. Each phase starts with failing tests, then implements the smallest change that makes those tests pass. No learner pass/fail scoring will be enabled by this plan.

## 1. Scope and safety rules

This plan fixes:

1. unauthenticated access to expert-reference and bundle-management endpoints;
2. path traversal through record and bundle identifiers;
3. exposure of raw recordings and reviewer metadata;
4. unbounded capture input and comparison workload;
5. forged feedback requests;
6. race-prone local JSON writes and failures from corrupt local files;
7. misleading readiness states;
8. the image-reference loading race and missing image provenance; and
9. accidental versioning of raw recordings and temporary research artifacts.

It does not:

- add a database or cloud deployment;
- establish validation thresholds or learner scoring;
- treat a self-reported reviewer code as proof of expert identity;
- alter the professional source facts in `knowledge-graph/`; or
- delete existing tracked research files automatically.

The resulting security boundary is deliberately local: FastAPI continues to bind to `127.0.0.1`. A secret held only in an ignored `.env` file protects developer/expert write operations. Before a multi-user or public deployment, replace this local token mechanism with real user authentication and role management.

## 2. Phase 1 — Define protected API roles and private response shapes

### Problem

The API lets any caller create, approve, supersede, bundle, activate, list, and download reference material. CORS only controls browser cross-origin requests; it does not authenticate direct requests.

### Tests first

Add API tests proving that:

- public capture and knowledge-graph routes remain available without credentials;
- every write route returns `401` without a token and `403` for an invalid token;
- a valid expert token may create candidate references and specifications;
- a valid reviewer/admin token is required to approve, supersede, and activate a bundle;
- public catalog/readiness responses never include image data, raw events, reviewer notes, reviewer codes, or activation history;
- private list, retrieval, manifest, and bundle routes require a valid authorized token; and
- error responses do not reveal token values, local paths, raw input, or private metadata.

### Implementation

1. Add a small FastAPI security dependency that reads a bearer token from `Authorization`.
2. Load tokens only from environment variables, for example `BAYBAYIN_EXPERT_TOKEN` and `BAYBAYIN_REVIEWER_TOKEN`; document names in `.env.example`, never values.
3. Enforce the least privilege needed for each route. Capture checks and graph lookup stay public; all reference-library data is protected.
4. Split API response schemas into public target/readiness summaries and authorized developer records.
5. Keep the current `127.0.0.1` server command in the README and explicitly prohibit `0.0.0.0` for this development mode.

### Done when

An unauthenticated caller cannot change, list, or download expert-reference material, and reviewer identity comes from the authenticated role rather than a request body field.

## 3. Phase 2 — Constrain identifiers and filesystem access

### Problem

`record_id` and `bundle_id` are interpolated into file paths. On Windows a value containing `..\\` can resolve outside the intended directory.

### Tests first

Add repository and endpoint tests proving that:

- only generated record IDs (`ref-` plus UUID hex) and bundle IDs matching the defined schema are accepted;
- malformed IDs, forward slashes, backslashes, `..`, encoded separators, and overly long values return `422` or `404` without reading a file;
- every repository read and write resolves inside its intended records, bundles, or specifications directory;
- a request cannot read `active-bundles.json`, manifests, graph files, or any sibling JSON file; and
- a valid existing record/bundle still resolves normally.

### Implementation

1. Define named regular expressions for record, bundle, target, and specification identifiers.
2. Validate path parameters at the FastAPI boundary and validate again in the repository layer.
3. Build paths through one helper that resolves the candidate and confirms it remains under the expected directory before access.
4. Use generated identifiers internally; never accept caller-selected file names for new records.

### Done when

No request-controlled string can select a file outside its designated repository directory.

## 4. Phase 3 — Bound and validate all capture work

### Problem

PNG safety is bounded, but canvas dimensions, coordinate ranges, event count, stroke count, and expensive comparison output can still be excessive.

### Tests first

Add model/API tests proving that:

- canvas width and height have documented maximums compatible with the 640×400 capture canvas;
- every coordinate is finite and falls within its declared canvas bounds, allowing only a small documented pointer tolerance if required;
- samples over the event, stroke, pointer-type, timestamp-span, and payload limits are rejected with `422`;
- degenerate valid dot strokes continue to work;
- preview rejects an over-limit request before DTW/form comparison;
- response comparison evidence is capped and cannot grow with raw event count; and
- malformed or extreme numeric values never produce `500`, `NaN`, or non-finite JSON.

### Implementation

1. Establish conservative named limits based on the capture UI and document their rationale.
2. Add cross-field sample validation for coordinates, canvas dimensions, stroke count, and event count.
3. Preserve PNG decoder limits already present and apply the same validation path to capture, import, reference creation, and preview.
4. Keep DTW input resampling fixed and cap returned alignment evidence or return a concise measurement summary.
5. Add a FastAPI request-body size limit appropriate to the maximum accepted sample.

### Done when

Malformed or unusually large samples fail predictably before expensive processing, while ordinary pen, mouse, touch, and dot-stroke recordings remain accepted.

## 5. Phase 4 — Make feedback server-derived

### Problem

`POST /api/feedback` accepts arbitrary error labels from the caller, which permits feedback that looks validator-derived even when no validator produced those errors.

### Tests first

Add tests proving that:

- feedback generated from a server validation result explains only that result's supported errors;
- arbitrary client error lists cannot create a mistake explanation;
- a missing, expired, cross-target, or unauthorized result reference returns a safe unavailable response;
- unavailable/provisional validation evidence does not become a learner error message; and
- source references remain limited to the selected target's graph evidence.

### Implementation

1. Change the feedback contract to accept a server-created validation-result identifier, or compute feedback in the preview route from the result created there.
2. Store only short-lived, non-sensitive validation evidence in an in-memory local result store; include target and active bundle IDs in the record.
3. Make feedback retrieve the stored evidence and ignore caller-supplied error arrays.
4. Retain deterministic feedback and the existing future-AI validation contract.

### Done when

Every feedback message is traceable to server-generated evidence for the same target and reference bundle.

## 6. Phase 5 — Make the file repository resilient and auditable

### Problem

Concurrent JSON writes use the same `.tmp` filename and can overwrite one another. A malformed local JSON file can also break catalog/readiness and return a server error.

### Tests first

Add tests proving that:

- simultaneous record creation, manifest generation, and activation preserve all valid data;
- activation history is append-only and no activation is silently lost;
- writes use unique temporary files and leave no partial JSON after an interrupted write;
- malformed record, bundle, specification, manifest, or active-registry JSON is isolated and reported as an authorized developer diagnostic;
- public catalog/readiness remains available if unrelated local reference data is corrupt; and
- corrupt or missing active-bundle state makes preview safely unavailable instead of returning `500`.

### Implementation

1. Add a process-local repository lock around read-modify-write operations.
2. Write through a uniquely named temporary file in the same directory, flush it, then atomically replace the target.
3. Validate loaded JSON against a versioned schema before it is used.
4. Quarantine or report invalid local files through protected developer diagnostics; do not include their contents in public errors.
5. Regenerate manifests from validated records only.

### Done when

An interrupted or malformed local file cannot corrupt unrelated records or take down public graph and preview endpoints.

## 7. Phase 6 — Clarify evidence lifecycle and activation integrity

### Problem

`reference_ready` currently means an approved record and specification exist, even if no active bundle is available for comparison.

### Tests first

Add tests proving that:

- readiness separately reports candidate, approved-reference, active-bundle, annotation-ready, and calibration-ready states;
- only an approved record paired with an approved matching specification can produce a bundle;
- only an authorized reviewer can activate an approved bundle;
- a superseded record or invalid bundle immediately becomes unavailable for preview;
- an active bundle also requires its matching approved specification; and
- preview never selects a bundle by file ordering.

### Implementation

1. Replace the single ambiguous readiness value with explicit evidence-state flags or a documented lifecycle enum.
2. Validate the full active chain at resolution time: target, record, specification, bundle, and later annotation/configuration.
3. Keep immutable source records and retain activation history, but do not expose that history publicly.
4. Update developer UI labels so “approved reference”, “active comparison bundle”, and “scoring calibrated” are distinct.

### Done when

Users and developers can see exactly what evidence exists without confusing approval with runnable validation.

## 8. Phase 7 — Fix and document the image-reference layer

### Tests first

Add frontend tests proving that:

- toggling the guide does not change the exported PNG or stroke events;
- switching targets before an image loads cannot draw the previous target's guide;
- a missing image produces an accessible, non-blocking status message;
- the five vowels use the correct asset mapping; and
- every core knowledge-graph target has exactly one declared image asset.

### Implementation

1. Give each image draw request a generation token and draw only when it matches the current target and visible state.
2. Handle image load failure and reset canvas alpha in `finally`-style logic.
3. Add `knowledge-graph/image-references.json` with each asset filename, source document identifier, PDF page, crop/reproduction method, and applicable target ID.
4. Add a test that compares the manifest with the current-release graph targets and public assets.

### Done when

The guide is reliable, never contaminates saved samples, and has source traceability suitable for the thesis methodology.

## 9. Phase 8 — Classify repository artifacts and documentation

### Tasks

1. Review `hurry-strokes/`, `tmp/`, and `temp.txt` with the team. Move intentional public fixtures into a clearly named test-fixture directory with a README; remove accidental temporary files in a separate, reviewed commit.
2. Do not treat the tracked stroke samples as expert ground truth unless their provenance, consent, and review status are documented.
3. Extend `.gitignore` for future exports, raw recording directories, generated manifests, local diagnostics, and `.env` files while preserving `.env.example`.
4. Update `app/README.md`, `docs/SYSTEM_DOCUMENTATION.md`, `docs/FILE_REFERENCE.md`, and `docs/flow.md` with the authorization boundary, private-data handling, endpoint access rules, limits, lifecycle states, and guide provenance.

## 10. Verification

After every phase, run focused tests first. At completion run:

```powershell
# From app\backend
.\.venv\Scripts\python.exe -m pytest -q --basetemp .tmp\pytest
.\.venv\Scripts\python.exe -m py_compile main.py reference_library.py multimodal.py feedback.py validation_evidence.py

# From app\frontend
npm.cmd test
npm.cmd run build
npm.cmd audit --omit=dev --offline
```

Manual checks using synthetic data only:

1. Run the app on `127.0.0.1`; confirm protected routes reject missing and invalid tokens.
2. Attempt record and bundle path traversal payloads using both slash styles; confirm no file data is returned.
3. Submit maximum valid and just-over-limit samples; confirm controlled `422` responses.
4. Create, approve, bundle, and activate one synthetic reference; confirm only authorized roles can perform each transition.
5. Confirm public catalog/readiness responses contain no image, event, note, reviewer, or activation-history data.
6. Rapidly change target while the image guide is loading; confirm only the selected guide appears and downloaded PNG remains guide-free.

## 11. Recommended implementation order

1. Endpoint authorization and private response schemas.
2. Identifier/path confinement.
3. Capture limits and feedback integrity.
4. Atomic repository writes and corrupt-file handling.
5. Evidence lifecycle/readiness clarity.
6. Image-guide reliability and provenance.
7. Repository artifact cleanup and documentation.

This order closes the ability to alter or disclose professional reference material before the team imports real expert recordings.
