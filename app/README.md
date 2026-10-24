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

## Review a saved recording

With both servers running, use **Open saved sample** to select a JSON file previously downloaded by the prototype. The review area shows its label, recording time, original canvas dimensions, and number of pen contacts. Select **Replay saved strokes** to watch the recorded events in order; you can stop the replay or close the sample. The review canvas is separate from the current drawing, which remains available while you review.

The importer accepts version 1 JSON files up to 32 MiB, with canvas dimensions from 1 to 1,000,000 pixels in each direction. It checks the sample using the local FastAPI server and draws the recorded events at a uniform scale. If the file cannot be opened or checked, the current drawing and previously opened sample remain available. The app does not save or change the imported file. Pen contacts are recorded pen-down events, not confirmed correct strokes; opening or replaying a sample does not validate its writing.

## Developer reference library

The local developer workflow is available at **http://127.0.0.1:3000/developer-reference-library** while both services are running. It imports a checked version 1 drawing JSON, attaches source and review metadata, and saves the result as a **candidate** reference. It accepts the knowledge graph's current 12 selected targets: **A, E, I, O, U, ba, be, bi, bo, bu, b, b_**.

Set `BAYBAYIN_REFERENCE_TOKEN` before starting FastAPI. The developer-library page asks for this local token once per browser session and sends it only to the local API. Keep it private; it protects reference records, bundles, specifications, manifests, and review actions. Capture and knowledge-graph routes do not require it.

Candidate recordings are not validator ground truth. The developer library accepts the current release's 12 selected targets from the knowledge graph. A developer can mark a recording approved only after adding a matching expert-approved character specification with a version, reviewer code, and decision date. The library can list and replay stored recordings and produces a graph-ready `manifest.json` for approved reference records.

The library stores recordings and its manifest in `app/data/reference-library/`, which Git ignores. Back up that directory using the team’s approved private storage; do not commit real recordings, non-public reviewer details, or the generated manifest. This local route has no authentication and is for a developer-controlled computer only. A deployed research or learner system will need authenticated storage and an approved retention policy.

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
