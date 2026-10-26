# Implementation plan: grounded AI learner feedback

**Status:** Proposed — no provider, credential, or runtime behavior changes are made by this plan.  
**Goal:** Add optional AI explanations that make deterministic results friendlier without allowing AI to decide Baybayin correctness.

## 1. Fixed decision boundary

The deterministic validator remains the sole authority for form, stroke, kudlit, and hybrid outcomes.

```text
learner drawing → deterministic result → source retrieval → AI explanation or fallback
```

AI may explain only confirmed validator error codes. It must never change pass/fail, choose a reference bundle, set thresholds, inspect raw expert recordings, invent errors/citations, or expose internal data.

AI feedback runs only for `prototype_result` and future calibrated results that have confirmed error codes. It does not run for `unavailable` or `practice_comparison` results.

## 2. Phase 1 — safe feedback context and deterministic fallback

Build a server-owned context from an already-computed result:

```json
{
  "resultState": "prototype_result | calibrated_result",
  "targetId": "ba",
  "language": "en | fil",
  "confirmedErrors": ["wrong_form", "trajectory_mismatch"],
  "branchStates": {"form": "needs_practice", "stroke": "needs_practice"},
  "sourceRefs": ["lopez-2025-pdf#pdf-page=56"],
  "imageReferenceIds": ["core-character-chart-part-1"]
}
```

Exclude PNG data, pointer events, raw measurements, reference bundle IDs, reviewer details, passwords, tokens, browser prompts, and arbitrary learner text.

First improve deterministic feedback to return up to three prioritized actions:

1. stroke count/order;
2. missing/misplaced/wrong kudlit;
3. direction/trajectory;
4. form.

Every response labels whether it is a prototype observation or approved calibrated finding.

### Tests first

- Unavailable/practice-only results cannot produce an AI request.
- Unknown error codes, raw image/event data, private IDs, and browser-supplied errors are excluded.
- Deterministic retrieval uses only the target’s committed knowledge-graph sources.
- Missing sources and unknown errors produce safe fallback feedback.

## 3. Phase 2 — constrained provider adapter

Keep all model calls in FastAPI, behind a small provider-neutral interface:

```text
generate(context) -> structured explanation
```

Do not call a model directly from the Next.js learner page. The backend owns the validation result and keeps credentials private.

If later deployed through Vercel, use a server-side AI Gateway/AI SDK integration with current documented model configuration. Otherwise use the same adapter behind server-only environment variables. Do not hard-code provider keys or model IDs.

The existing `ai_feedback.py` request/response validator is the starting contract. Extend its structured output to require:

```json
{
  "message": "One concise encouraging explanation.",
  "detectedErrors": ["trajectory_mismatch"],
  "correctiveActions": ["Follow the curve in one continuous movement."],
  "sourceRefs": ["lopez-2025-pdf#pdf-page=56"],
  "needsReview": false,
  "language": "en"
}
```

Validation rules:

- one to three bounded corrective actions;
- errors are a subset of confirmed deterministic errors;
- citations are a subset of retrieved source refs;
- language is requested `en` or `fil`;
- verdict language or new target claims are rejected; and
- invalid, timed-out, or unavailable AI always falls back to deterministic feedback.

### Tests first

- Accept valid structured output.
- Reject invented errors/citations, malformed JSON, missing fields, unsupported language, excessive text, or verdict language.
- Provider timeout/network failure produces fallback within the request time budget.
- Model output cannot override form/stroke/hybrid state.
- Source/PDF prompt-injection-like text is treated as data, never instructions.

## 4. Phase 3 — API, UI, privacy, and controls

Create `POST /api/learner-feedback`. The browser sends only an opaque, short-lived validation-result ID. The server resolves safe evidence, retrieves sources, calls the adapter, validates output, and returns either `ai_grounded` or `deterministic_fallback`.

The learner page adds **Explain this feedback** below a deterministic result:

- deterministic outcome stays visible;
- loading text says AI explains but does not decide;
- show one explanation, up to three actions, and source refs;
- show fallback seamlessly when AI fails; and
- English first; enable Filipino after terminology review.

Security/privacy requirements:

- never send raw learner handwriting, expert images/events, names, or reviewer data to a provider;
- use server-only ignored credentials;
- set request/time/token limits and per-IP/local-session rate limiting;
- store only result ID, target, error codes, retrieved IDs, model/prompt version, latency, fallback, and output-valid status; and
- set retention/deletion rules before research deployment.

### Tests first

- Expired/unknown IDs and arbitrary payload fields are rejected.
- Rate limit, provider error, and timeout retain deterministic fallback.
- Logs contain no raw drawings, secrets, reviewer codes, or free-text learner input.
- UI handles success, fallback, timeout, and inaccessible states accessibly.

## 5. Phase 4 — Chapter 3 evaluation

Evaluate AI feedback separately from handwriting validation using a held-out, expert-labeled learner dataset. Qualified evaluators rate factual consistency, source correctness, corrective-action usefulness, clarity/tone, and language quality. Report these separately from form/stroke/kudlit/hybrid accuracy:

- feedback source correctness and relevance;
- unsupported-claim and fallback rates;
- mean/p95 feedback latency; and
- evaluator agreement.

Do not use feedback quality to claim better handwriting classification.

## 6. Implementation order and acceptance criteria

1. Finish deterministic feedback actions and safety tests.
2. Add short-lived safe result IDs.
3. Implement deterministic graph retrieval.
4. Add a fake provider and structured-output validation.
5. Add one server-side provider, credentials, timeouts, rate limits, and fallback.
6. Add learner UI explanation.
7. Evaluate feedback separately before thesis claims.

Done when AI cannot affect deterministic results, every explanation is traceable to confirmed errors and approved sources, failures fall back safely, no raw handwriting leaves the backend, and the feedback layer has separate Chapter 3 evidence.
