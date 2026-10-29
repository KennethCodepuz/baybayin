# Current system status

**Last updated:** 2026-10-28
**System stage:** Local thesis prototype with preliminary hybrid model validation and an experimental centerline-based model.

This document is the source of truth for what the running application can and cannot claim. Implementation plans describe intended work; they do not automatically describe delivered behavior.

## What learners can do now

1. Open the home page or `/learn`, choose one of 12 supported targets, and draw on an 800×600 canvas.
2. Use the centered 4-column × 3-row visual grid as a guide. It is not saved or scored. Space above and below the grid remains drawable for kudlit and other marks.
3. Show or hide the source-backed guide, undo a completed stroke, clear the attempt, and submit **Check my practice**.
4. Receive non-persisting, preliminary model validation against the matching expert recording: separate form, stroke-count, stroke-process, and applicable kudlit outputs. The browser does not receive the expert PNG, pointer events, reviewer data, reference IDs, or calibration values.
5. For a scored prototype target with a detected error, select **Explain this feedback**. The result is deterministic by default. A configured AI Gateway may rewrite only the same confirmed errors and source references; it cannot change the result.

## Current target coverage

All 12 current-release targets have expert recordings used as canonical comparison references: `a`, `e`, `i`, `o`, `u`, `ba`, `be`, `bi`, `bo`, `bu`, `b`, and `b_`.

| Learner state | Targets | What the system does |
|---|---|---|
| `preliminary_model_validation` | All 12, when the local deployment-model artifact is present | Uses the fixed `pilot-v1` image and stroke features against the matching expert recording. It returns separate model outputs for form, count, process, and applicable kudlit/cancellation-mark validation. |
| `prototype_result` | `a`, `ba`, `e`, `i`, `o`, `u` | Applies local prototype form and DTW limits derived from the accepted `ajstrokes` and `hurry-strokes` recordings. It can return a practice match or needs-more-practice result. |
| `practice_comparison` | `be`, `bi`, `bo`, `bu`, `b`, `b_` | Compares the learner form and ordered strokes with the active expert recording, but deliberately cannot label the attempt correct or incorrect. |

The model is trained on controlled group-protocol attempts and compared against expert reference recordings. Its learner-facing output is preliminary. If the Git-ignored local model artifact is unavailable, the endpoint falls back to the prior deterministic learner behavior.

When present, the local `pilot-centerline-v2` artifact is preferred over the prior multi-output model. It substitutes a symmetric centerline distance for the mask-IoU model input and uses glyph-normalized endpoint displacement. In controlled writer-separated tests across 54 current recordings, form-output changes fell from 9 to 0 for whole-symbol translations and from 10 to 4 for width variations. Pen-width sensitivity therefore remains. The candidate's pilot form precision decreased slightly, while its form and kudlit recall increased; these results rely on provisional group labels and three writers, not final expert-reviewed ground truth.

## What is actually validated

- **Image form:** visible-ink normalization and mask-overlap measurements.
- **Stroke process:** preserved `down` / `move` / `up` stroke boundaries, stroke count, constrained Dynamic Time Warping (DTW) for path strokes, and normalized point-distance comparison for dot strokes.
- **Kudlit support:** the canvas preserves marks outside the grid, and an approved per-target annotation can check full-canvas above/below placement. It is not a complete calibrated kudlit validator for every modified target yet.
- **Feedback:** deterministic feedback is constrained to the validator's confirmed error codes and the selected knowledge-graph source references.
- **Preliminary model:** four reference-relative weighted-forest outputs classify likely form, count, process, and applicable kudlit issues. Their image and stroke measurements are returned only as internal evidence, not exposed to learners.

## What the system cannot claim yet

- It cannot give a final research-grade correct/incorrect verdict for `be`, `bi`, `bo`, `bu`, `b`, or `b_`.
- It cannot claim final expert-reviewed accuracy, precision, recall, F1-score, confusion matrices, or population performance. Those require a frozen, expert-labeled held-out dataset.
- It does not yet support all Baybayin characters, unrestricted words, transliteration, handwriting recognition, user accounts, a database, cloud deployment, participant consent collection, or research-data retention workflows.
- It does not expose expert samples or treat learner attempts as new threshold data.
- The optional AI explanation feature is not validation AI. It cannot inspect handwriting, set thresholds, add errors, select references, or decide correctness. It remains deterministic-fallback only until a valid AI Gateway key and current model ID are configured.

## Developer workflow

`/developer` is a locally password-gated workspace. Developers can capture JSON recordings, replay them, inspect validation evidence, and manage the local Git-ignored expert-reference library. The backend additionally requires `BAYBAYIN_REFERENCE_TOKEN` for protected reference-management routes. These controls are appropriate only for a developer-controlled localhost prototype, not a deployed study system.

## Next evidence needed

1. Collect accepted calibration samples for `be`, `bi`, `bo`, `bu`, `b`, and `b_`, including kudlit/cancellation-mark variations.
2. Have the Baybayin expert review the samples, expected stroke rules, allowable variants, and resulting form/DTW/kudlit thresholds.
3. Freeze versioned calibration configurations separately from the eventual held-out evaluation dataset.
4. Collect writer-disjoint, expert-labeled held-out data before reporting Chapter 3/4 metrics.
