# Baybayin drawing capture prototype

This prototype uses a Next.js frontend and a FastAPI backend. It loads the repository's source-traceable knowledge graph, records a selected target, a final image, and ordered pointer events, and can reopen and replay saved recordings. The backend checks that recordings are structurally complete; neither component validates Baybayin characters or stroke rules yet.

## Run on this Windows computer

If `backend\.venv` or `frontend\node_modules` is missing, run the first-time setup below before starting the services. Then open **two PowerShell terminals** and leave both running.

In the first terminal, start FastAPI:

```powershell
cd '.\backend'
py -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
$env:BAYBAYIN_REFERENCE_TOKEN = 'choose-a-long-random-local-token'
.\.venv\Scripts\python.exe -m uvicorn main:app --host 127.0.0.1 --port 8000
```

In the second terminal, start Next.js:

```powershell
cd '.\frontend'
npm.cmd run dev -- --hostname 127.0.0.1
```

Open **http://127.0.0.1:3000** in Chrome or Edge. Select a target such as `ba`; its faint reference image appears behind the 600×450 drawing canvas for tracing. The canvas includes a 4-column × 3-row grid of twelve equal 150×150 squares. Draw over the guide and select **Download sample**. The grid and image guide are separate visual layers and are not included in the saved learner image or stroke events. The target comes from the committed knowledge graph but is not a correctness check. Stop each server with Ctrl+C in its terminal.

## Learner practice

Open **http://127.0.0.1:3000/learn** for the learner-facing practice page. It uses the same 800×600 canvas and centered 4×3 developer grid, including clear space above and below the grid for kudlit and other marks. It has an optional guide, Undo stroke, Try again, and **Check my practice**. The page sends the current drawing to the local backend but does not save it or expose expert recordings, reference IDs, developer controls, or JSON downloads.

The root URL, **http://127.0.0.1:3000/**, now opens this learner page. Select **Go to developer tools**, enter `ganbatte`, then use `/developer` to reach the protected reference-library and validation-inspector links. This is a local prototype access gate; the separate `BAYBAYIN_REFERENCE_TOKEN` remains required for reference-record API actions and a deployed system needs real user authentication.

Developers use the protected **Record calibration sample** link (`/developer/capture`) to collect grid-based JSON recordings for threshold/calibration work. Do not automatically treat learner practice attempts as calibration data: an expert must review and label any sample before it may influence prototype or research thresholds.

The verified expert batch is now the active local reference set for all 12 current targets. The learner page therefore performs a clearly labeled **practice comparison** against the matching expert image and ordered stroke recording. For prototype-only testing, local calibration configurations were derived from the supplied `ajstrokes/` and `hurry-strokes/` samples for `a`, `ba`, `e`, `i`, `o`, and `u`; these targets show a **Prototype match** or **Prototype result: needs more practice**. Those thresholds are not expert-approved research thresholds and must be replaced by expert-labeled calibration before thesis evaluation.

## Deterministic validator preparation

The backend now supports protected, expert-approved stroke annotations at `POST /api/stroke-annotations`. An annotation binds a target and reference bundle to explicit expected stroke data and, for modified characters, an outside-grid kudlit/cancellation-mark stroke and normalized full-canvas region. The validator can therefore distinguish an approved above-grid mark from the same mark below the grid during a practice comparison. It does not make a learner verdict until calibration is approved.

Use [the deterministic validator plan](deterministic-validator-implementation-plan.md) when preparing the first `ba`, `be`, and `bo` reviewer annotations. Store annotations locally in `app/data/reference-library/annotations/`; they are Git-ignored research records.

## Review a saved recording

With both servers running, use **Open saved sample** to select a JSON file previously downloaded by the prototype. The review area shows its label, recording time, original canvas dimensions, and number of pen contacts. Select **Replay saved strokes** to watch the recorded events in order; you can stop the replay or close the sample. The review canvas is separate from the current drawing, which remains available while you review.

The importer accepts version 1 JSON files up to 32 MiB, with canvas dimensions from 1 to 1,000,000 pixels in each direction. It checks the sample using the local FastAPI server and draws the recorded events at a uniform scale. If the file cannot be opened or checked, the current drawing and previously opened sample remain available. The app does not save or change the imported file. Pen contacts are recorded pen-down events, not confirmed correct strokes; opening or replaying a sample does not validate its writing.

## Developer reference library

The local developer workflow is available at **http://127.0.0.1:3000/developer-reference-library** while both services are running. It imports a checked version 1 drawing JSON, attaches source and review metadata, and saves the result as a **candidate** reference. It accepts the knowledge graph's current 12 selected targets: **A, E, I, O, U, ba, be, bi, bo, bu, b, b_**.

Set `BAYBAYIN_REFERENCE_TOKEN` before starting FastAPI. The developer-library page asks for this local token once per browser session and sends it only to the local API. Keep it private; it protects reference records, bundles, specifications, manifests, and review actions. Capture and knowledge-graph routes do not require it.

Candidate recordings are not validator ground truth. The developer library accepts the current release's 12 selected targets from the knowledge graph. A developer can mark a recording approved only after adding a matching expert-approved character specification with a version, reviewer code, and decision date. The library can list and replay stored recordings and produces a graph-ready `manifest.json` for approved reference records.

### Import the supplied expert batch

The repository includes a reviewed, checksum-backed manifest at `app/research/expert-reference-batch-2026-10-24.json` for the 12 originals in the private top-level `expert reference/` directory. On `/developer-reference-library`, select **Preflight 12 expert recordings** first. Every file must have the expected SHA-256 fingerprint, target, safe PNG, complete events, and current-release target before importing is enabled. Then select **Import verified candidates** and enter a non-identifying developer/importer code.

Import copies the recordings into the Git-ignored local library with immutable filename, original-file checksum, source-canvas, collection-date, and batch provenance. It does not alter the originals, approve a reference, create a bundle, activate validation, or produce learner scores. Select an imported record to replay it and review its provenance; then use the existing specification → approval → bundle → activation workflow.

The library stores recordings and its manifest in `app/data/reference-library/`, which Git ignores. Back up that directory using the team’s approved private storage; do not commit real recordings, non-public reviewer details, or the generated manifest. The developer endpoints require the local token but are still intended only for a developer-controlled computer. A deployed research or learner system will need user authentication, secure storage, and an approved retention policy.

## First-time setup on another computer

Install Python 3.10 or newer and Node.js 20.9 or newer. Then run the following from the `app` directory:

```powershell
cd backend
py -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
cd ..\frontend
npm.cmd install
```

Start each service as shown above, using the corresponding `app\backend` and `app\frontend` paths on that computer. Do not open an HTML file directly; Next.js serves the page.

## Tests

Run these in separate terminals from their respective directories:

```powershell
# From app\backend
.\.venv\Scripts\python.exe -m pytest -q

# From app\frontend
npm.cmd test
```

## Sample format and data handling

The downloaded JSON includes a version, UTC creation time, manually entered target, 600×450 canvas dimensions, PNG data URL, and ordered events. Event coordinates are in canvas pixels relative to its upper-left corner; timestamps are browser event timestamps in milliseconds relative to the browser's time origin, not wall-clock times. Each event includes its pointer type. Stroke boundaries are preserved. Use 600×450 for every final expert and learner recording so the evaluation dataset has one consistent capture layout. The FastAPI endpoint returns the sample but does not save it. Identifiers and consent handling are not implemented, so use test data only until a research protocol is approved. The browser may rename repeated downloads; manage exported files carefully.

The prototype listens on localhost and is for development only. Reference sources, permissions, character specifications, and an expert-approved stroke rubric are documented as pending in `research/reference-and-rubric.md`.

## Knowledge graph

The curated source data lives in `../knowledge-graph/` and is loaded by FastAPI as read-only data. It exposes these local endpoints:

- `GET /api/knowledge-graph/catalog` for the 12 current-release targets;
- `GET /api/knowledge-graph/targets/{id}` for a target's source-backed details; and
- `GET /api/knowledge-graph/readiness` for the evidence state of every target.
- `POST /api/learner-validation` for a learner-safe, non-persisting practice result.

Readiness means whether a candidate and approved expert reference exist. It never enables learner scoring in this version; `scoringAvailable` remains `false` for every target. Graph changes are repository changes and must be reviewed with their source references. Do not edit the graph through the browser or store private review data in it.

## Multimodal validation infrastructure

Open **http://127.0.0.1:3000/developer-validation** to load a checked sample and inspect the separate image-form, JSON-stroke, and hybrid response contracts. It deliberately reports `scoring unavailable` until an expert has approved a matching reference bundle and thresholds.

An expert recording already includes both modalities: the sample's `image` is the final PNG and `events` are the ordered stroke events. Once an approved reference recording and matching specification exist, `POST /api/reference-bundles` can create a versioned bundle with a normalized canonical image and reproducible stroke features. `POST /api/validation/preview` returns the safe unavailable-state contract, while `POST /api/feedback` returns source-grounded fallback feedback from supplied validator error codes.

The current feedback implementation is deterministic. It is the safety boundary for a future AI provider: any model must receive only structured validator errors and retrieved source references, and it may explain those errors but cannot change validation outcomes.

## Algorithm and evaluation readiness

The backend now includes developer-only, pure algorithm modules for the next validation phase. `stroke_matching.py` normalizes and resamples ordered strokes, then produces constrained Dynamic Time Warping (DTW) distance and alignment evidence. `stroke_rules.py` evaluates stroke-count, direction, and start/end-region rules only when an approved annotation is supplied. `form_matching.py` produces normalized PNG mask-overlap and centroid measurements. Preview can show their provisional evidence for an active bundle, but they do not independently decide whether a learner is correct.

Recorded PNG data is decoded and bounded before the backend accepts it. The local developer library keeps new bundles inactive until an expert reviewer explicitly activates one; preview uses only that active bundle. Existing legacy bundles remain inactive and require review before they can provide comparison evidence.

`validation_config.py` only accepts a matching, expert-approved calibration configuration before `scoring.py` can turn measurements into form or stroke outcomes. The tracked [configuration example](config/calibration.schema.example.json) is deliberately provisional and cannot enable scoring.

For the later Chapter 3/4 dataset, use the schemas and separation procedure in [evaluation](evaluation/README.md). The metric utility calculates accuracy, precision, recall, F1-score, and per-error confusion-matrix counts once expert-labeled held-out samples exist. Actual evaluation results belong in Chapter 4.

## Documentation

- [System documentation](docs/SYSTEM_DOCUMENTATION.md)
- [File reference](docs/FILE_REFERENCE.md)
- [System flow](docs/flow.md)
