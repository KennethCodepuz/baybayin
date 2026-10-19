# Implementation plan: import and replay a saved drawing

**Status:** Proposed plan; no feature implementation is included in this document.  
**Goal:** Let a reviewer open a JSON sample previously downloaded from the app, inspect its target and recording details, and replay its strokes.  
**Approach:** Test-driven development: write or update each relevant test, confirm it fails for the intended reason, implement the smallest change, and run the tests again.

## 1. Scope and current state

The Next.js frontend currently captures and replays a drawing in the current session. It sends the sample to FastAPI's `POST /api/samples/check` endpoint before downloading JSON. The endpoint checks the sample's structure but does not save it or judge the writing. The app cannot yet open a saved JSON recording.

This feature adds a **read-only review area** for an imported sample, separate from the current drawing canvas. Importing, replaying, or clearing a reviewed sample must not overwrite a drawing in progress. It supports the app's current version 1 JSON exports and their recorded timestamps, event sequence, target, and original canvas dimensions.

This phase does not add Baybayin correctness scoring, expert labels, a database, automatic PDF extraction, or a permanent file library. The supplied PDF and expert-reviewed rubric will guide later validation work.

## 2. Reviewer workflow

1. The reviewer opens the app and selects **Open saved sample** in the review area.
2. The browser reads one selected JSON file locally, checks its size and JSON syntax, and sends the parsed sample to the existing local FastAPI endpoint for structural validation.
3. If validation succeeds, show the target, recorded canvas dimensions, capture date, stroke count, and a rendered view of the recorded strokes. Label this as an imported recording, not a correctness result.
4. The reviewer selects **Replay strokes** to animate the recorded events in order using the recorded timing. **Stop replay** ends playback and restores the full rendered drawing. A separate **Close sample** control clears only the review area.
5. If import fails or the backend is unreachable, show an understandable error and keep any previously opened review sample and current drawing intact. The reviewer can select another file and retry.

The selected file is read from the user's device; its contents are sent only to the configured local backend for checking. Neither the browser nor backend persists the imported sample as part of this feature. The original downloaded file is never modified.

## 3. Data and behavior decisions

### Format and validation

- Use the existing version 1 sample schema: `version`, `createdAt`, `target`, `canvas`, `image`, and ordered `events`, each with event type, position, timestamp, and pointer type.
- Reuse `POST /api/samples/check` so download and import share one structural check. Handle malformed JSON, missing or invalid fields, unsupported versions, incomplete or impossible stroke sequences, and unordered timestamps with clear messages.
- Check file size before reading it; set and document a reasonable cap during implementation, and explain when a file is too large. Align any additional limits with current exports and cover boundary cases in tests.
- Reuse the backend's existing event-count and image-string limits. Its current image check verifies the data-URL shape, not that the PNG depicts the event sequence; do not claim otherwise. Render the review drawing from events so replay and full-stroke view use the same source.
- Preserve the imported event order and values, target, timestamp values, and original dimensions in review state. Do not silently normalize, relabel, or resave the source. The endpoint may serialize numeric representations differently; preservation means equivalent values, not byte-for-byte JSON identity.
- Accept existing app-generated 640 × 400 exports. For other valid dimensions, display the events using uniform scaling and centering so aspect ratio and relative positions are preserved; do not allocate an unbounded canvas based on file-supplied dimensions. Decide and document safe dimension limits, with clear errors for unsupported values.
- Define one recorded stroke as a `down` event followed by any `move` events and an `up` event, matching the current capture format. This count describes pen contacts; whether it is an acceptable Baybayin stroke count remains an expert decision.

### Playback and safety of work in progress

- Replay relative event times from the first recorded event. Multiple strokes, dots, pen lifts, and pauses must remain visible in their recorded order.
- Block duplicate import submissions and handle file selection or backend errors without replacing a valid review sample. Selecting a new file during playback must not leave an animation running against the wrong sample.
- Stop or cancel replay on close and component cleanup. Starting a new replay or stopping one must leave the review canvas in a predictable state.
- Keep the current drawing canvas and its controls independent of imported review state. A failed import must preserve both the current drawing and any previous valid review sample. The selected file's native contents remain untouched.
- Treat labels and error text as text, not HTML. Restrict this workflow to local sample files and the existing localhost backend; do not add third-party uploads.

## 4. TDD work sequence

### Step 1 — Establish sample validation tests

1. Add FastAPI tests for representative version 1 exports and failure cases not already covered: unsupported version, missing required data, empty events, duplicate `down`, stray `up` or `move`, and multiple valid strokes including a dot.
2. Add or adjust validation only where a test shows the existing endpoint cannot meet the agreed import contract. Do not claim the endpoint validates character correctness or PNG/event consistency.

**Done when:** The shared endpoint accepts supported recordings and rejects malformed ones consistently, with the tests passing.

### Step 2 — Test and implement sample loading

1. Write frontend tests for JSON parsing, size limits, backend success and failure responses, unsupported files, and preservation of an already loaded sample on errors. Use fixtures based on the existing export shape.
2. Implement file selection and safe loading into separate review state. The file reader must not replace a current sample until all validation succeeds.
3. Show target, date, dimensions, and pen-contact count. Make empty, loading, success, and error states understandable to the reviewer.

**Done when:** A valid existing export opens; errors are actionable; neither current work nor the prior review sample is lost on failure.

### Step 3 — Test and implement review rendering and replay

1. Write tests for event ordering, multiple strokes, a dot, relative timing, display scaling, stopping playback, and replay cleanup. Verify that the input event data is not mutated.
2. Render from the imported events on the separate review canvas. Fit different supported source dimensions without distortion, and retain the original stored coordinates.
3. Add replay, stop, and close actions using the review state. Reuse existing drawing logic where this can be done without changing the behavior of the current capture canvas.

**Done when:** The reviewer can see and replay a saved sample and close it without changing the recording or drawing in progress.

### Step 4 — Verify the complete workflow and document it

1. Run the frontend and backend automated tests and a Next.js production build.
2. In a real browser, draw and export a sample; open that JSON; check its metadata and replay; stop and replay again. Confirm multiple strokes and a dot work, and that existing drawing data remains intact.
3. Verify malformed JSON, an unsupported version, an incomplete stroke, an oversized file, and an unavailable backend show useful errors without replacing a prior valid sample.
4. Update the app README with startup, import, replay, expected data handling, and feature limitations. Record any browser or device checks that could not be performed.

**Done when:** Automated checks pass and the browser-to-FastAPI-to-review flow works end to end for a genuine app-exported file.

## 5. Acceptance criteria

- A JSON file exported by the current app can be reopened and replayed in sequence.
- Target, date, original dimensions, and recorded pen-contact count are shown without asserting correctness.
- Supported non-default dimensions render without changing aspect ratio or original coordinates.
- Invalid, oversized, unsupported, or unavailable-backend cases show an error and preserve existing work.
- Stopping, restarting, closing, or changing the reviewed sample does not leave a stale animation or alter the drawing in progress.
- The app and backend do not persist or modify the selected file.
- Tests are written before the corresponding implementation, existing tests continue to pass, and the full browser flow is checked.

## 6. After this feature

Have the qualified reviewer assess the draft [ba and ka specifications](research/ba-ka-pilot-character-specifications.md), make reference drawings, and review their imported replays. The reviewer must resolve the meaning of the PDF's numbered marks and acceptable pen lifts before we implement stroke-correctness checks.
