# Baybayin validator system documentation

## Purpose and current scope

This project is a **developer-only Baybayin handwriting-reference system**. It collects a drawing as two connected forms of evidence:

- an ordered sequence of pen events for stroke analysis; and
- a PNG image of the completed character for form analysis.

It helps the research team collect, review, preserve, and prepare expert references. It does **not** currently tell a learner that a Baybayin drawing is correct or incorrect. Scoring requires real expert-approved references, annotations, and calibration thresholds.

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

The downloaded sample contains `version`, `createdAt`, `target`, canvas dimensions, a PNG data URL, and ordered `down`, `move`, and `up` events. The backend verifies PNG bytes and limits image size before accepting it.

### 2. Review and replay a saved sample

Use **Open saved sample** on the capture page. The system validates the JSON with FastAPI, displays recording metadata, and replays the ordered events. Replay demonstrates what was recorded; it is not handwriting validation.

### 3. Create an expert reference

1. Open `/developer-reference-library`.
2. Load a checked sample JSON.
3. Save it as a candidate reference with source and review metadata.
4. Create an approved character specification.
5. Approve the candidate only after it matches that specification.
6. Create a multimodal reference bundle.
7. An expert reviewer explicitly activates one approved bundle for the target.

A bundle preserves the original approved sample and derived data: normalized image, stroke features, target/source links, and review data. Bundles are immutable. Activation is stored separately so old bundles remain auditable and cannot be selected accidentally.

### 4. Inspect provisional validation evidence

Open `/developer-validation` and load a checked sample.

- If there is no active bundle, the page reports that reference activation is pending.
- If an active bundle exists, the page displays the sample PNG and shows provisional image-form and stroke evidence.
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
| `POST /api/validation/preview` | Return unavailable or provisional form/stroke evidence. |
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

1. Expert-created recordings for pilot characters.
2. Expert approval of a reference bundle and activation decision.
3. Approved structural annotations where required.
4. Expert-approved calibration thresholds for image and DTW evidence.
5. Expert-labeled held-out samples for Chapter 3/4 evaluation metrics.

See [FILE_REFERENCE.md](FILE_REFERENCE.md) for the role of each project file.
