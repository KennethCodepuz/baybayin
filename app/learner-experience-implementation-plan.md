# Implementation plan: learner practice and validation experience

**Status:** Proposed — no runtime behavior changes are made by this plan.  
**Goal:** Create a learner-facing Baybayin practice experience that captures handwriting safely, requests the hybrid validator, and explains only evidence the system is authorized to claim.  
**Method:** Test-driven development. Each phase begins with failing tests, followed by the smallest implementation that satisfies them.

## 1. Current starting point

The project already has the technical foundation for the validator:

- a 600×450 capture canvas with a visual-only 4×3 grid;
- a final PNG plus ordered `down`/`move`/`up` stroke events;
- normalized image-form measurements;
- constrained DTW stroke comparison and structural stroke evidence;
- a hybrid evidence contract;
- source-grounded deterministic feedback; and
- a scoring module that only accepts an approved calibration configuration linked to an active expert bundle.

The 12 supplied expert recordings (`a`, `e`, `i`, `o`, `u`, `ba`, `be`, `bi`, `bo`, `bu`, `b`, `b_`) are currently imported as **candidate** records. They are not yet approved references, active bundles, or scoring templates.

Therefore, this work must separate three learner states:

| State | What learner sees | What the system may say |
| --- | --- | --- |
| Practice unavailable | No active expert bundle | “This character is being prepared; try another available character.” |
| Practice comparison | Active expert bundle but no approved calibration | “Here is a practice comparison,” with measurements and non-judgmental guidance; never correct/incorrect. |
| Calibrated validation | Active bundle and matching expert-approved calibration | A form result, stroke result, hybrid result, and feedback tied to explicit validator findings. |

No UI wording, color, icon, or AI message may imply correctness in the first two states.

## 2. Scope and non-goals

### Included

1. A separate learner route and focused practice workflow.
2. Safe capture, retry, submission, result display, and accessibility behavior.
3. A learner-validation API that uses only an explicitly active expert bundle.
4. Clear unavailable/provisional/calibrated result contracts.
5. Server-generated, source-grounded feedback based on actual validator findings.
6. Test data and evaluation hooks needed for Chapter 3/4.

### Not included in this phase

1. User accounts, a database, public deployment, or permanent learner-data storage.
2. Automatic promotion of an expert candidate to approved/active status.
3. Invented DTW, image, stroke-count, or kudlit thresholds.
4. A general AI model deciding whether a character is correct.
5. Claims of accuracy, precision, recall, F1, or research success before held-out expert-labeled evaluation.

## 3. Phase 0 — complete the evidence gate first

The learner interface can be built before this gate completes, but a real comparison for a target cannot begin until the target reaches the required state.

### Required reviewer workflow per target

1. Inspect the imported candidate’s replay, PNG, target, source references, and provenance.
2. Create a versioned approved character specification from the knowledge graph.
3. Approve or reject the candidate with reviewer code, date, and notes.
4. Create its immutable multimodal reference bundle.
5. Explicitly activate the approved bundle.
6. For scored validation later, approve a calibration configuration tied to that exact bundle and algorithm versions.

For `be`, `bi`, `bo`, `bu`, `b`, and `b_`, the reviewer must confirm the knowledge-graph kudlit form and position before approving the character specification.

### Tests first

- A target without an active bundle is unavailable to learner comparison.
- A candidate, rejected record, inactive bundle, wrong-target bundle, or superseded reference is never selected.
- A calibration belonging to another target, bundle, or algorithm version is rejected.
- No response can include `correct`, `incorrect`, `passed: true`, or `passed: false` without the complete approved gate.

### Done when

The API can deterministically report each target’s exact learner state without relying on UI assumptions.

## 4. Phase 1 — learner route and guided drawing experience

### Interface

Create `/learn` as a separate route from the developer capture and review pages. It should provide:

1. a simple character chooser that labels each target as **available for practice**, **calibrated**, or **being prepared**;
2. the source-backed target label and a short instruction;
3. an optional reference-image guide and the existing 4×3 visual-only square grid;
4. a 600×450 drawing area, Clear, Undo stroke, and Try again controls;
5. visible keyboard instructions and a no-pointer/unsupported-input message;
6. a single **Check my practice** action; and
7. a dedicated result panel rather than developer JSON, checksum, bundle ID, or raw measurement views.

The grid and guide must remain outside the saved PNG and event stream. The learner route must not expose developer-review controls, expert recordings, tokens, raw reference JSON, or private provenance.

### Tests first

- The route offers only current-release targets returned by the API.
- Grid and image-guide pixels do not enter the submitted sample.
- Submit remains disabled for empty/incomplete drawings and becomes available only for a structurally complete sample.
- Clear and Undo affect the current learner drawing only.
- A target marked unavailable cannot be submitted for comparison.
- Keyboard focus, labels, live status messages, and adequate touch targets work without relying on color alone.

### Done when

A learner can draw and resubmit a character without downloading or handling JSON files, while developer tooling remains separate.

## 5. Phase 2 — learner-validation API contract

### API design

Add a public, write-free endpoint such as `POST /api/learner-validation`.

Input:

```json
{ "sample": "the existing version-1 Sample object" }
```

The endpoint will:

1. validate the existing strict sample schema and PNG limits;
2. resolve the canonical target through the knowledge graph;
3. resolve only the deliberately active bundle for that target;
4. calculate form and stroke evidence when an active bundle exists;
5. load only a matching approved calibration configuration before scoring; and
6. return a minimal learner-safe result.

The endpoint will not persist the sample, return the expert PNG/events, expose private record IDs, accept a bundle ID from the browser, or accept browser-supplied error codes or thresholds.

### Result contract

Use an explicit discriminated state instead of ambiguous nullable fields:

```json
{
  "state": "unavailable | practice_comparison | calibrated_result",
  "target": "ba",
  "message": "human-readable safe status",
  "form": { "state": "unavailable | provisional | pass | needs_practice" },
  "stroke": { "state": "unavailable | provisional | pass | needs_practice" },
  "hybrid": { "state": "unavailable | provisional | pass | needs_practice" },
  "feedback": { "items": [] },
  "sourceRefs": []
}
```

Only `calibrated_result` may contain pass/needs-practice outcomes. `practice_comparison` may return carefully rounded, non-score-like observations (for example, “your first stroke starts farther right than the reference”) generated by approved deterministic rules.

### Security and resilience requirements

- Preserve current size, coordinate, timestamp, event-count, and PNG checks.
- Do not log or save raw learner drawings by default.
- Rate-limit the public validation endpoint before any network deployment; use an in-memory local limit during development and platform-level controls in deployment.
- Return bounded, generic errors for malformed samples and never leak filesystem paths, tokens, private source files, or stack traces.
- Use server-owned target/bundle/calibration resolution only.
- Add request IDs and short-lived aggregate timing/error telemetry without identity or drawing content.

### Tests first

- Malformed, oversized, incomplete, out-of-bounds, wrong-target, and unsafe-PNG samples return controlled errors.
- A browser cannot choose an inactive or different target bundle.
- Missing bundle returns only `unavailable`.
- Active bundle without calibration returns only `practice_comparison` and cannot contain correctness language.
- A matching approved calibration enables exactly the approved scoring branches.
- Feedback is derived only from server-produced validation findings.
- The endpoint never writes learner samples to the reference library.

### Done when

The learner UI has one safe endpoint whose result changes only when server-owned evidence readiness changes.

## 6. Phase 3 — feedback that teaches without inventing conclusions

### Deterministic feedback first

Map specific validator findings to short guidance, such as:

- stroke count differs;
- stroke order differs;
- first/last stroke direction differs;
- kudlit is missing, misplaced, or uses the wrong form;
- overall form needs another attempt.

Every item must state whether it is a **practice observation** or a **calibrated validation finding**. Show one to three prioritized items, an optional “show reference guide” action, and source references where appropriate.

### Optional AI explanation later

If the thesis includes AI-generated wording, add it only as a constrained explanation layer after deterministic feedback is stable:

1. send the model structured, server-produced findings plus retrieved source snippets;
2. forbid it from producing scores, new error categories, or decisions;
3. validate its returned schema and fall back to deterministic text;
4. record prompt/model version, retrieval IDs, latency, fallback use, and output-validation status; and
5. evaluate feedback relevance separately from handwriting accuracy.

This makes the system AI-assisted for explanation, while the actual validation remains deterministic and reproducible.

### Tests first

- Unknown error codes never become fabricated advice.
- Provisional evidence cannot render verdict language.
- Feedback has no private expert data or hidden chain-of-thought.
- AI adapter failure always returns deterministic fallback feedback.

## 7. Phase 4 — calibration and learner validation enablement

This is the decisive research phase, not merely a UI task.

### Dataset protocol

Create three strictly separate private datasets:

| Dataset | Purpose | May influence thresholds? |
| --- | --- | --- |
| Expert references | Templates and specifications | No direct threshold tuning from the same recordings alone |
| Calibration set | Expert-labeled learner attempts, including common errors | Yes |
| Held-out evaluation set | Expert-labeled attempts from separate writers/sessions | No — used only for final Chapter 3/4 reporting |

Collect consented, anonymized learner attempts using the learner route’s fixed 600×450 layout. The expert labels form, stroke count, order, direction, and kudlit placement separately. Include both acceptable variation and intentional/common errors.

### Calibration procedure

1. Start with a small pilot target set—preferably the `b` family already covered by the expert batch.
2. Produce form, DTW, stroke-count/order/direction, and kudlit measurements for calibration samples.
3. Select thresholds and decision logic on the calibration set only.
4. Have the expert approve the thresholds, annotation/rubric version, algorithm version, and reference-bundle IDs.
5. Store the approval as a versioned calibration configuration; do not place personal learner data in Git.
6. Enable `calibrated_result` only for targets whose exact active bundle has a matching approved calibration.

### Tests first

- The scorer rejects a calibration with missing reviewer provenance, invalid numbers, incompatible algorithm version, or wrong reference bundle.
- Changing the active bundle disables the old calibration automatically.
- A target can be calibrated while all other targets remain practice-only.
- A complete calibrated result records which form/stroke/hybrid rule produced the outcome.

## 8. Phase 5 — Chapter 3 evaluation and reporting support

Build an evaluator that runs separately from the live learner route.

For each held-out expert-labeled attempt, retain:

- anonymized sample ID and split (`calibration` or `held_out`);
- target and expected expert labels;
- active bundle and calibration IDs;
- form, stroke, and hybrid outputs;
- error-specific labels for form, count, order, direction, and kudlit placement;
- retrieval/feedback relevance labels, if RAG/AI feedback is evaluated; and
- response-time measurement if practical feedback speed is a research objective.

Report separately for form validator, stroke validator, and hybrid validator:

- accuracy, precision, recall, and F1-score;
- confusion matrices;
- error-specific outcomes for form, count, order, direction, and kudlit placement;
- RAG source correctness and feedback relevance, when applicable; and
- latency distribution.

Never use held-out results to retune thresholds; if retuning becomes necessary, create a new held-out set or declare the original result exploratory.

## 9. Development order

1. Complete reviewer approval, specifications, bundles, and activation for a pilot target (`ba` first is simplest; then the `b` family).
2. Implement and test the learner route in unavailable/practice-only mode.
3. Implement and test the learner-safe validation API and result contract.
4. Implement deterministic learner feedback and accessibility review.
5. Run usability checks with synthetic samples—no correctness claims.
6. Collect independently expert-labeled calibration attempts.
7. Approve calibration and enable calibrated results only for pilot targets.
8. Expand target coverage, then collect the held-out evaluation set and produce Chapter 3/4 metrics.

## 10. Acceptance criteria

- Learners can select, draw, clear/undo, and submit a character without accessing developer artifacts or JSON downloads.
- Every learner result clearly states one of: unavailable, practice comparison, or calibrated validation.
- No target shows correctness language without an active expert bundle and matching approved calibration.
- The browser cannot select private expert references, a bundle, a threshold, or feedback findings.
- Learner samples are not persisted by default, and reference/evaluation data remain separated.
- The result view gives useful, source-grounded guidance for actual form/stroke/kudlit findings.
- The project can separately evaluate form, stroke, hybrid, and feedback components against expert-reviewed held-out ground truth.
