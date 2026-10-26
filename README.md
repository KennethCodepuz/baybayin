# Baybayin Validator Prototype

This is a local Baybayin handwriting-validator thesis prototype built with a Next.js frontend and a Python FastAPI backend. It compares a learner drawing with a matching active expert recording using both the final PNG and ordered pointer events.

Read [the current system status](app/docs/CURRENT_SYSTEM_STATUS.md) before relying on any result. It is the authoritative boundary between implemented prototype behavior and unimplemented research claims.

## What the prototype does now

- Lets learners draw any of 12 current targets on the guided 800×600 canvas and submit a non-persisting practice attempt.
- Compares the final form and ordered strokes with the active local expert recording using normalized image measurements, stroke count, dot-position comparison, and constrained DTW.
- Gives prototype practice results for `a`, `ba`, `e`, `i`, `o`, and `u` using local prototype limits derived from accepted calibration recordings.
- Gives a comparison-only result for `be`, `bi`, `bo`, `bu`, `b`, and `b_`, because those targets have no scoring threshold yet.
- Preserves outside-grid drawing space for kudlit and other marks; approved annotations can evaluate above/below placement where available.
- Captures, downloads, imports, and replays version 1 JSON recordings for developer/reference work.
- Keeps a private local developer reference library with provenance, review, bundle, and activation records.
- Provides deterministic source-constrained feedback. An optional server-side AI explanation layer can only rephrase confirmed errors and falls back safely when unavailable.

## What it does not do yet

- Make research-grade correct/incorrect claims for `be`, `bi`, `bo`, `bu`, `b`, or `b_` until expert-reviewed calibration thresholds are created.
- Report accuracy, precision, recall, F1, confusion matrices, or error-detection rates until a writer-disjoint expert-labeled held-out dataset is collected.
- Validate every Baybayin character, unrestricted words, or transliterations.
- Let an AI model decide correctness, inspect raw handwriting, set thresholds, or override deterministic results.
- Include production authentication, a database, cloud storage, participant consent, or research-data retention workflows.

## Requirements

- Windows PowerShell
- Python 3.10 or newer
- Node.js 20.9 or newer

If the backend virtual environment or frontend dependencies are not present, install them from the `baybayin` directory:

```powershell
cd '.\app\backend'
py -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt

cd '..\frontend'
npm.cmd install
```

## Run the project

Open two PowerShell terminals.

Start the FastAPI backend in the first terminal:

```powershell
cd '.\app\backend'
py -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m uvicorn main:app --host 127.0.0.1 --port 8000
```

Start the Next.js frontend in the second terminal:

```powershell
cd '.\app\frontend'
npm.cmd run dev -- --hostname 127.0.0.1
```

Open these pages in a browser:

| Page | Purpose |
| --- | --- |
| `http://127.0.0.1:3000` | Learner practice: draw, compare, and receive a safe result. |
| `http://127.0.0.1:3000/developer-login` | Local developer access gate; the prototype password is `ganbatte`. |
| `http://127.0.0.1:3000/developer` | Developer workspace, capture, reference library, and validation inspector links. |

Stop either service with `Ctrl+C` in its terminal.

## Developer reference workflow

1. A qualified Baybayin writer draws a current-release target using the developer capture page.
2. Download the checked JSON sample.
3. Open the developer reference library and load that JSON file.
4. Add the source page, convention, input method, reviewer code, and notes.
5. Save it as a **candidate reference**.
6. After expert review, create the approved character-specification version.
7. Approve only recordings linked to that specification version.

Reference data is stored locally in `app/data/reference-library/`. Git ignores this directory so real recordings, manifests, and non-public review metadata are not committed. Back it up using the team’s approved private storage.

The local developer area has a prototype password gate and protected backend reference routes. It remains suitable only for a developer-controlled local computer.

## Tests

Run the backend tests:

```powershell
cd '.\app\backend'
.\.venv\Scripts\python.exe -m pytest -q
```

Run the frontend tests and production build:

```powershell
cd '.\app\frontend'
npm.cmd test
npm.cmd run build
```

## Next milestone

Collect and obtain expert review for calibration samples for `be`, `bi`, `bo`, `bu`, `b`, and `b_`; then create versioned thresholds without using the held-out evaluation data. See [the current system status](app/docs/CURRENT_SYSTEM_STATUS.md).
