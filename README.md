# Baybayin Validator Prototype

This is an early development prototype for a Baybayin writing validator. It uses a Next.js frontend and a Python FastAPI backend.

The system currently records a drawing and its ordered pen or pointer events. Developers can save those recordings as JSON, replay them later, and curate expert-reviewed examples for a future validator. It does not yet decide whether a Baybayin character, stroke order, or stroke direction is correct.

## What the prototype does now

- Captures mouse, pen, or touch drawing events on a canvas.
- Records stroke boundaries, coordinates, timestamps, pointer type, target label, and a final PNG image.
- Checks the structural completeness of a recording through FastAPI.
- Downloads a version 1 JSON drawing sample.
- Opens a saved JSON sample and replays its recorded strokes.
- Provides a local developer reference library for `ba` and `ka` recordings.
- Stores candidate references with source, capture, review, checksum, and provenance metadata.
- Requires an approved character-specification version before a candidate can become an approved reference.
- Exports a graph-ready manifest of approved reference recordings.

## What it does not do yet

- Validate whether a learner wrote Baybayin correctly.
- Determine the correct stroke count, order, direction, pen lifts, or acceptable handwriting variations.
- Use the PDF or physical book automatically as a validation engine.
- Include user accounts, authentication, cloud storage, or a database.

The `ba` and `ka` writing rules remain pending expert review. Until a qualified reviewer approves a specification and reference recordings, no recording should be treated as ground truth.

## Requirements

- Windows PowerShell
- Python 3.10 or newer
- Node.js 20.9 or newer

Dependencies are already installed in this workspace. For a fresh computer, install the requirements first:

```powershell
cd 'C:\path\to\Thesis-writing\app\backend'
py -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt

cd '..\frontend'
npm.cmd install
```

## Run the project

Open two PowerShell terminals.

Start the FastAPI backend in the first terminal:

```powershell
cd 'C:\Users\Kenne\OneDrive\Documents\ChatGPT\Thesis-writing\app\backend'
.\.venv\Scripts\python.exe -m uvicorn main:app --host 127.0.0.1 --port 8000
```

Start the Next.js frontend in the second terminal:

```powershell
cd 'C:\Users\Kenne\OneDrive\Documents\ChatGPT\Thesis-writing\app\frontend'
npm.cmd run dev -- --hostname 127.0.0.1
```

Open these pages in a browser:

| Page | Purpose |
| --- | --- |
| `http://127.0.0.1:3000` | Capture a drawing, download a sample, and replay saved samples. |
| `http://127.0.0.1:3000/developer-reference-library` | Import and curate developer reference recordings for `ba` and `ka`. |

Stop either service with `Ctrl+C` in its terminal.

## Developer reference workflow

1. A qualified Baybayin writer draws `ba` or `ka` using the capture page.
2. Download the checked JSON sample.
3. Open the developer reference library and load that JSON file.
4. Add the source page, convention, input method, reviewer code, and notes.
5. Save it as a **candidate reference**.
6. After expert review, create the approved character-specification version.
7. Approve only recordings linked to that specification version.

Reference data is stored locally in `app/data/reference-library/`. Git ignores this directory so real recordings, manifests, and non-public review metadata are not committed. Back it up using the team’s approved private storage.

The developer reference route has no authentication, so use it only on a developer-controlled local computer.

## Tests

Run the backend tests:

```powershell
cd 'C:\Users\Kenne\OneDrive\Documents\ChatGPT\Thesis-writing\app\backend'
.\.venv\Scripts\python.exe -m pytest -q
```

Run the frontend tests and production build:

```powershell
cd 'C:\Users\Kenne\OneDrive\Documents\ChatGPT\Thesis-writing\app\frontend'
npm.cmd test
npm.cmd run build
```

## Next milestone

Find a qualified Baybayin expert, approve the `ba` and `ka` character specifications, and collect several reviewed reference recordings. That reference set will support the first limited stroke-comparison validator.
