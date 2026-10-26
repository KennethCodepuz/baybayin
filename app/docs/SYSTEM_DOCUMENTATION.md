# Baybayin validator system documentation

## Purpose and current scope

This project is a **local learner-practice and developer-reference Baybayin handwriting prototype**. It collects a drawing as two connected forms of evidence:

- an ordered sequence of pen events for stroke analysis; and
- a PNG image of the completed character for form analysis.

It lets learners submit a practice drawing and preserves separate developer workflows for creating and reviewing references. Expert comparison bundles are active for the 12 current-release targets. Prototype scoring is available only for `a`, `ba`, `e`, `i`, `o`, and `u`; `be`, `bi`, `bo`, `bu`, `b`, and `b_` remain comparison-only until calibration thresholds are reviewed. See [CURRENT_SYSTEM_STATUS.md](CURRENT_SYSTEM_STATUS.md) for the authoritative capability boundary.

## Architecture

```text
Next.js browser interface
  |  capture, replay, import, review
  v
FastAPI local API
  |  checks samples, stores developer reference records,
  |  produces bundles and provisional evidence
  v
Local developer reference library (Git-ignored)
  |  records, specifications, bundles, active-bundle registry
  v
Committed knowledge graph
  |  character catalog, source references, image-source manifest
```

The frontend runs on `http://127.0.0.1:3000`. The FastAPI backend runs on `http://127.0.0.1:8000`. Both are intended for the same developer-controlled computer.

## Main workflows

### 1. Capture a drawing

1. Open the capture page at `/`.
2. Choose a source-backed core character.
3. Draw with a pen, mouse, or touch input.
4. Download the JSON sample.

The downloaded sample contains `version`, `createdAt`, `target`, 800×600 canvas dimensions, a PNG data URL, and ordered `down`, `move`, and `up` events. The capture page displays a centered visual-only 4-column × 3-row grid; it is not part of the saved PNG or events. The backend verifies PNG bytes and limits image size before accepting it.

### 2. Review and replay a saved sample

Use **Open saved sample** on the capture page. The system validates the JSON with FastAPI, displays recording metadata, and replays the ordered events. Replay demonstrates what was recorded; it is not handwriting validation.

### 2a. Learner practice

`/learn` is separate from developer capture and reference-review pages. A learner selects a source-backed target and draws on the same 800×600 canvas and centered visual-only 4×3 grid used by developer capture. The surrounding area remains drawable for kudlit and other marks outside the base-character grid. Learners may show/hide the guide, undo the latest completed stroke, clear the drawing, and select **Check my practice**. The browser sends the in-memory sample to `POST /api/learner-validation`; it does not persist the sample or reveal expert recordings, bundle IDs, measurements, tokens, or developer metadata.

The learner response has one explicit state: `unavailable` when no active expert bundle exists, `practice_comparison` when a bundle exists without calibration, or `prototype_result` for a local prototype calibration. The verified expert batch is active locally for the 12 current targets. The supplied `ajstrokes/` and `hurry-strokes/` recordings derive prototype-only form/DTW limits for `a`, `ba`, `e`, `i`, `o`, and `u`; this is explicitly not an expert-approved research result. `be`, `bi`, `bo`, `bu`, `b`, and `b_` therefore remain practice comparison until separately calibrated, particularly because their kudlit/cancellation marks need approved outside-grid data.

When a `prototype_result` contains confirmed errors, the backend creates a short-lived feedback-result ID. **Explain this feedback** resolves that ID server-side and returns deterministic source-constrained feedback. If `AI_GATEWAY_API_KEY` and a current `AI_GATEWAY_MODEL` are configured, the server may request an explanation from AI Gateway. It sends no PNG, pointer events, expert sample, reviewer data, bundle ID, or threshold values; the returned text is validated against the same allowed errors and sources. Provider failures return deterministic feedback instead.

### 3. Create an expert reference

1. Open `/developer-reference-library`.
2. Load a checked sample JSON.
3. Save it as a candidate reference with source and review metadata.
4. Create an approved character specification.
5. Approve the candidate only after it matches that specification.
6. Create a multimodal reference bundle.
7. An expert reviewer explicitly activates one approved bundle for the target.

A bundle preserves the original approved sample and derived data: normalized image, stroke features, target/source links, and review data. Bundles are immutable. Activation is stored separately so old bundles remain auditable and cannot be selected accidentally.

### 3a. Import the supplied expert batch

The `expert reference/` directory is treated as private source material. The committed `research/expert-reference-batch-2026-10-24.json` contains the allowed filenames, expected target IDs, non-identifying expert code, source references, and SHA-256 fingerprints. The developer page exposes protected preflight and import actions for this one declared batch.

Preflight validates **all** entries with the same `Sample` schema as the API before a record is written: filename containment, bytes checksum, JSON, PNG safety, stroke order/bounds, manifest target match, and current knowledge-graph eligibility. Import makes a candidate copy only when the full batch passes. Every saved record carries immutable batch provenance, including its original filename and checksum. Re-importing is idempotent by sample checksum.

The batch is not automatically trusted: each candidate still needs a matching approved specification, an explicit review decision, a bundle, and explicit activation before developer preview can compare against it.

### 4. Inspect provisional validation evidence

Open `/developer-validation` and load a checked sample.

- If an active bundle exists, the page displays the sample PNG and shows image-form and stroke comparison evidence. The current local expert batch provides active bundles for all 12 current targets.
- If a future target has no active bundle, the page reports that reference activation is pending.
- Stroke evidence uses constrained Dynamic Time Warping (DTW) for path strokes and point-distance comparison for stationary dot strokes.
- The page still reports **scoring unavailable** until an expert-approved calibration configuration exists.

## Validation layers

### PNG safety and form evidence

The backend accepts only real PNG data, with bounded encoded size, width, height, and pixel count. It normalizes the visible ink onto a fixed square canvas, then can calculate developer-only image evidence:

- mask intersection-over-union (IoU);
- centroid distance;
- normalized ink bounds; and
- image checksums.

These values are measurements, not pass/fail rules.

### Stroke evidence

Stroke events preserve pen-down and pen-up boundaries. The system extracts stroke count, normalized points, start/end positions, direction, path length, and bounds.

For comparison, it:

1. normalizes the full glyph for translation and uniform scale;
2. resamples non-dot paths by arc length;
3. uses a constrained DTW alignment for matching path strokes;
4. compares dot strokes by their normalized center position; and
5. returns structured evidence without a correctness decision.

### Structural rules and scoring

Future structural checks require a complete, approved annotation that identifies the target, reference bundle, reviewer, date, version, expected stroke count, and optional direction/start/end regions.

Future scoring requires a matching approved calibration configuration. It rejects empty, malformed, non-finite, or incomplete comparison evidence. A scorer cannot pass a stroke without comparing every required stroke.

### Kudlit placement rules

For an approved modified-target annotation, the deterministic mark evaluator uses the learner event stream’s full canvas-normalized coordinates. It checks the annotation’s chosen mark stroke against its approved above/below region; an outside-grid mark is therefore retained rather than cropped away by full-image normalization. The evaluator can return provisional `misplaced_kudlit` evidence, but a learner verdict still requires the associated calibration record.

## Knowledge graph and sources

`knowledge-graph/` is committed, source-traceable research data. It contains the core character catalog, source-register metadata, relationship graph, orthography rules, diacritics, and visual-source manifest. It is read-only from the browser.

The visual reference pages are source material from the Lopez/KWF publication. They do not become handwritten templates or thresholds until a qualified expert approves a recorded reference and any required annotation.

## API summary

| Endpoint | Purpose |
|---|---|
| `POST /api/samples/check` | Validate a version 1 capture sample and safe PNG. |
| `GET /api/knowledge-graph/catalog` | List source-backed core targets. |
| `GET /api/knowledge-graph/readiness` | Show candidate/approval readiness. |
| `POST /api/references` | Save a candidate developer reference. |
| `PATCH /api/references/{id}/review` | Approve, reject, or supersede a reference. |
| `POST /api/specifications` | Save a character specification. |
| `POST /api/reference-bundles` | Create an immutable bundle from approved evidence. |
| `POST /api/reference-bundles/{id}/activate` | Select the single active expert bundle for its target. |
| `GET /api/reference-batches/expert-2026-10-24/preflight` | Verify every declared private expert source before any import. |
| `POST /api/reference-batches/expert-2026-10-24/import` | Copy the verified batch into candidate records; requires an importer code. |
| `GET /api/reference-batches/expert-2026-10-24/coverage` | Show `active`, `approved_inactive`, `candidate`, or `missing` for each core target. |
| `POST /api/validation/preview` | Return unavailable or provisional form/stroke evidence. |
| `POST /api/learner-validation` | Return a learner-safe, non-persisting unavailable, practice-comparison, or prototype result. |
| `POST /api/learner-feedback` | Resolve a short-lived server result ID into deterministic feedback or a validated optional AI explanation. |
| `POST /api/stroke-annotations` | Save a protected, approved stroke/kudlit annotation tied to an existing reference bundle. |
| `POST /api/feedback` | Produce deterministic, source-constrained feedback. |

## Data locations and privacy

`app/data/reference-library/` is Git-ignored. It stores local expert samples, bundles, specifications, manifests, and active-bundle history. Back it up only in the team’s approved private storage. Do not commit recordings, real reviewer identities, consent records, API keys, or credentials.

The committed knowledge graph should contain source facts and public source references only. Use anonymous writer/reviewer codes in research records.

## Running locally

Start FastAPI in one PowerShell terminal:

```powershell
cd 'C:\Users\Kenne\OneDrive\Documents\ChatGPT\Thesis-writing\app\backend'
.\.venv\Scripts\python.exe -m uvicorn main:app --host 127.0.0.1 --port 8000
```

Start Next.js in another:

```powershell
cd 'C:\Users\Kenne\OneDrive\Documents\ChatGPT\Thesis-writing\app\frontend'
npm.cmd run dev -- --hostname 127.0.0.1
```

Open `http://127.0.0.1:3000`.

## Testing

```powershell
# app\backend
.\.venv\Scripts\python.exe -m pytest -q

# app\frontend
npm.cmd test
npm.cmd run build
```

When Next.js is inside a synced OneDrive directory, builds can occasionally fail while creating generated `.next` directories with Windows `EPERM`. Retry first; if it persists, run the project from a non-synced local folder or pause sync while building.

## What is still needed before real validation

1. Accepted calibration samples and reviewed thresholds for `be`, `bi`, `bo`, `bu`, `b`, and `b_`.
2. Approved structural/kudlit annotations where required.
3. Expert-labeled writer-disjoint held-out samples for Chapter 3/4 evaluation metrics.
4. A valid AI Gateway key and current model ID if optional AI phrasing is to be enabled.

See [FILE_REFERENCE.md](FILE_REFERENCE.md) for the role of each project file.
