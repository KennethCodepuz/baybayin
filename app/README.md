# Baybayin drawing capture prototype

This prototype uses a Next.js frontend and a FastAPI backend. It loads the repository's source-traceable knowledge graph, records a selected target, a final image, and ordered pointer events, and can reopen and replay saved recordings. The backend checks that recordings are structurally complete; neither component validates Baybayin characters or stroke rules yet.

## Run on this Windows computer

The dependencies have been installed in `frontend/node_modules` and `backend/.venv`. Open **two PowerShell terminals** and leave both running.

In the first terminal, start FastAPI:

```powershell
cd 'C:\Users\Kenne\OneDrive\Documents\ChatGPT\Thesis-writing\app\backend'
.\.venv\Scripts\python.exe -m uvicorn main:app --host 127.0.0.1 --port 8000
```

In the second terminal, start Next.js:

```powershell
cd 'C:\Users\Kenne\OneDrive\Documents\ChatGPT\Thesis-writing\app\frontend'
npm.cmd run dev -- --hostname 127.0.0.1
```

Open **http://127.0.0.1:3000** in Chrome or Edge. Select a core character such as `ka`, draw in the white box, and select **Download sample**. The target comes from the committed knowledge graph but is not a correctness check. Stop each server with Ctrl+C in its terminal.

## Review a saved recording

With both servers running, use **Open saved sample** to select a JSON file previously downloaded by the prototype. The review area shows its label, recording time, original canvas dimensions, and number of pen contacts. Select **Replay saved strokes** to watch the recorded events in order; you can stop the replay or close the sample. The review canvas is separate from the current drawing, which remains available while you review.

The importer accepts version 1 JSON files up to 32 MiB, with canvas dimensions from 1 to 1,000,000 pixels in each direction. It checks the sample using the local FastAPI server and draws the recorded events at a uniform scale. If the file cannot be opened or checked, the current drawing and previously opened sample remain available. The app does not save or change the imported file. Pen contacts are recorded pen-down events, not confirmed correct strokes; opening or replaying a sample does not validate its writing.

## Developer reference library

The local developer workflow is available at **http://127.0.0.1:3000/developer-reference-library** while both services are running. It imports a checked version 1 drawing JSON, attaches source and review metadata, and saves the result as a **candidate** reference. The pilot accepts only samples labelled `ba` or `ka`.

Candidate recordings are not validator ground truth. The developer library accepts the current release's 24 core targets from the knowledge graph. A developer can mark a recording approved only after adding a matching expert-approved character specification with a version, reviewer code, and decision date. The library can list and replay stored recordings and produces a graph-ready `manifest.json` for approved reference records.

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

The downloaded JSON includes a version, UTC creation time, manually entered target, canvas dimensions, PNG data URL, and ordered events. Event coordinates are in canvas pixels relative to its upper-left corner; timestamps are browser event timestamps in milliseconds relative to the browser's time origin, not wall-clock times. Each event includes its pointer type. Stroke boundaries are preserved. The FastAPI endpoint returns the sample but does not save it. Identifiers and consent handling are not implemented, so use test data only until a research protocol is approved. The browser may rename repeated downloads; manage exported files carefully.

The prototype listens on localhost and is for development only. Reference sources, permissions, character specifications, and an expert-approved stroke rubric are documented as pending in `research/reference-and-rubric.md`.

## Knowledge graph

The curated source data lives in `../knowledge-graph/` and is loaded by FastAPI as read-only data. It exposes these local endpoints:

- `GET /api/knowledge-graph/catalog` for the 24 current-release targets;
- `GET /api/knowledge-graph/targets/{id}` for a target's source-backed details; and
- `GET /api/knowledge-graph/readiness` for the evidence state of every target.

Readiness means whether a candidate and approved expert reference exist. It never enables learner scoring in this version; `scoringAvailable` remains `false` for every target. Graph changes are repository changes and must be reviewed with their source references. Do not edit the graph through the browser or store private review data in it.
