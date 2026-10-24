# Implementation plan: DTW stroke validation, form comparison, and evaluation readiness

**Status:** Proposed — no learner pass/fail scoring is enabled by this plan alone.  
**Goal:** Build the algorithmic and evaluation-ready layers of the Baybayin validator while expert reference recordings and expert calibration are pending.  
**Method:** Test-driven development (TDD). For every behavior, write a focused failing test first, implement the smallest change that passes it, then run the related suite before proceeding.

## 1. Current foundation

The project already provides a developer-only pipeline:

```text
canvas drawing
  -> version 1 JSON sample (ordered pen events + final PNG)
  -> saved/replayed/imported sample
  -> candidate / approved reference record
  -> approved specification
  -> immutable reference bundle
       - normalized 256 x 256 PNG
       - reproducible stroke features
       - source references
```

The knowledge graph provides the 12 selected character targets (A, E, I, O, U, ba, be, bi, bo, bu, b, and b_) and source-traceable material from *Pinagyamang Baybayin* (Lopez/KWF, 2025). It is a source layer, not a set of unapproved scoring rules.

The current preview endpoint safely reports that scoring is unavailable. This behavior must remain until experts approve reference bundles, annotations, and thresholds.

## 2. Scope and principles

This work adds an algorithmic baseline and research tooling, not a trained AI model.

It includes:

- stroke-aware Dynamic Time Warping (DTW);
- deterministic image-form measurements;
- separate form, stroke, and hybrid result contracts;
- configuration and provenance for future expert-approved thresholds;
- expert annotation and calibration artifacts;
- held-out evaluation and Chapter 3 metric tooling;
- constrained feedback that explains validator findings only.

It excludes:

- presenting synthetic data as Baybayin ground truth;
- final thresholds or public correctness claims without expert approval;
- training a machine-learning model before a sufficiently labeled dataset exists;
- collecting personal identifiers unless separately approved by the research protocol;
- a production database, authentication, or deployment.

## 3. Algorithm design

### 3.1 Stroke branch: constrained, multi-stroke DTW

Use the existing pen-event order as the primary stroke evidence.

For each corresponding expert and learner stroke:

1. Validate a complete `down -> move* -> up` event sequence.
2. Normalize points to the unit canvas, then normalize translation and scale using the full glyph bounds.
3. Resample each stroke by arc length to a fixed configurable point count. This makes the result independent of browser sampling frequency.
4. Apply DTW to the ordered `(x, y)` point sequences using Euclidean point distance.
5. Apply a configurable Sakoe–Chiba alignment band to prevent implausible time warping.
6. Keep the raw cumulative distance, normalized DTW distance, alignment path, and algorithm/configuration version as evidence.

Before DTW, run transparent rule checks for:

- stroke count;
- stroke order;
- gross start-region mismatch;
- gross end-region mismatch;
- dominant direction mismatch;
- optional kudlit stroke requirements when an approved annotation requires them.

A different stroke count or incompatible stroke sequence should produce explicit error codes rather than an opaque DTW number. DTW is then used for trajectory similarity within a matched stroke pair.

### 3.2 Form branch: deterministic visual comparison

Compare final PNGs separately from stroke events:

1. Use the existing PNG normalization process on both learner and expert image.
2. Produce derived binary ink masks using an explicitly versioned threshold.
3. Calculate transparent measurements such as ink bounding-box ratio, centroid displacement, intersection-over-union (IoU) of masks, and structural similarity (SSIM) where the dependency is approved.
4. Reserve localized checks, including kudlit-region overlap, for approved normalized-coordinate annotations.
5. Return all measurements as evidence; turn them into errors only after expert-approved criteria exist.

The form branch must not infer writing order. The stroke branch must not infer final form correctness from event order alone.

### 3.3 Hybrid policy

The hybrid decision combines independent branch states. It must retain every branch result and its evidence.

| Form | Stroke | Hybrid state |
|---|---|---|
| unavailable | unavailable | unavailable |
| available, pass | unavailable | unavailable |
| unavailable | available, pass | unavailable |
| available, pass | available, pass | pass only under an approved policy |
| available, fail | available, any | fail with form evidence |
| available, any | available, fail | fail with stroke evidence |
| uncertain | any | needs expert review |

The policy must have an ID/version and store the configuration versions used. No policy may produce a pass/fail until both branch criteria are explicitly approved.

## 4. Planned implementation phases

### Phase 0 — Define versioned algorithm contracts

**Tests first**

- Valid and invalid algorithm configuration schemas.
- Required provenance: reference bundle ID, configuration ID, feature version, image-normalization version, and algorithm version.
- Validation responses with `unavailable`, `needs_review`, `pass`, and `fail` states.
- Tests proving that missing or unapproved threshold configurations cannot return a pass/fail.

**Implementation**

- Add versioned, repository-tracked *template* configuration schemas under `knowledge-graph/` or a clearly named `app/config/` directory.
- Keep real expert calibration files outside Git if they include private review details; retain an anonymized version ID and approval metadata in the bundle.
- Extend the validation response evidence shape to record measurements and configuration provenance.

**Done when:** Every future result identifies exactly which reference bundle and algorithm/configuration version produced it.

### Phase 1 — Implement stroke canonicalization and DTW

**Tests first**

- Arc-length resampling preserves the first and last point.
- Translation and uniform scale changes produce equivalent normalized paths.
- A reversed path produces a higher distance and can be labeled as a direction error.
- The same geometric path with sparse versus dense point sampling gives a similar DTW result.
- Identical strokes yield zero or near-zero normalized distance.
- Distinct synthetic paths yield a larger distance.
- Multistroke matching preserves stroke order and rejects mismatched counts before DTW.
- Alignment-band validation rejects invalid parameters and prevents unbounded pathological alignment.

**Implementation**

- Add a pure `stroke_matching.py` module in the FastAPI backend.
- Implement `resample_by_arc_length`, glyph/stroke normalization, Euclidean distance, constrained DTW, and matched-stroke aggregation.
- Return measurements and alignment evidence without a pass/fail if the selected configuration is not expert-approved.
- Integrate the module behind the existing stroke-branch interface.

**Done when:** The backend can deterministically compare two well-formed synthetic stroke recordings, explain the comparison inputs, and remain non-judgmental without approved criteria.

### Phase 2 — Add structural stroke-rule checks

**Tests first**

- Wrong stroke count returns `wrong_stroke_count` before trajectory scoring.
- Swapped synthetic strokes return `wrong_stroke_order`.
- Reversed vertical and horizontal paths return `wrong_stroke_direction` when an approved expected direction is provided.
- Start/end region checks accept boundary values consistently.
- A kudlit requirement produces no error without an approved annotation and the appropriate explicit error only with one.

**Implementation**

- Add structural checks that take approved annotation/specification data as input.
- Store region definitions in normalized coordinates, never browser pixels.
- Return individual findings as evidence; do not collapse them into a single score.

**Done when:** Structural errors are deterministic, traceable to an approved rule, and separate from DTW trajectory distance.

### Phase 3 — Implement form-measurement baseline

**Tests first**

- Image normalization remains deterministic across transparency and white-background variants.
- Synthetic identical masks yield IoU 1 and near-identical structural measurements.
- Shifted, resized, missing-mark, and extra-mark synthetic masks produce expected relative measurement changes.
- Mask creation handles blank, malformed, and non-PNG input safely.
- Kudlit-region measurements only run with a matching approved annotation.

**Implementation**

- Add a pure `form_matching.py` module.
- Build binary masks and calculate image measurements (ink bounds, centroids, IoU, and optionally SSIM).
- If SSIM is adopted, pin its library version and capture it in the algorithm metadata; otherwise keep the baseline dependency-free.
- Integrate results into the existing form-branch response, remaining `unavailable` until an approved configuration is linked.

**Done when:** Form evidence can be generated reproducibly for synthetic image pairs without claiming a character is correct.

### Phase 4 — Add configurable branch scoring and hybrid decisions

**Tests first**

- Missing calibration remains unavailable even when measurements exist.
- An unapproved calibration file is rejected.
- Synthetic values at, below, and above a known test threshold produce the expected branch state.
- All combinations of form/stroke pass, fail, unavailable, and needs-review preserve both branch results.
- A hybrid result cannot overwrite branch error codes or claim pass when either branch is unavailable or uncertain.

**Implementation**

- Add a schema for approved threshold configurations containing: target ID, bundle ID/version, form metric limits, DTW limits, structural requirements, approval code, decision date, and configuration version.
- Add branch score adapters and a versioned hybrid policy module.
- Keep test-only configurations isolated from real expert calibration data.

**Done when:** A scoring decision can run only with a matching, approved expert configuration and can always be reproduced from stored evidence.

### Phase 5 — Improve developer review and expert annotation workflow

**Tests first**

- Candidate samples cannot be annotated as canonical without an approved specification.
- Annotations reject invalid normalized coordinates, unsupported error labels, missing reviewer code, or version mismatches.
- Reference records and bundles remain immutable after approval; a correction creates a new version.
- The interface shows the original replay, original PNG, normalized PNG, and extracted strokes as distinct evidence views.

**Implementation**

- Extend the developer reference library with a review view for the recorded image and replayed event path.
- Add annotation capture for required regions, optional/required kudlit regions, and approved structural expectations.
- Add a local calibration review form for experts to inspect candidate threshold behavior on examples. It must label every decision as provisional or approved.
- Add source and reviewer provenance to the saved annotation/calibration record.

**Done when:** An expert can review what the system will compare, approve a versioned reference/annotation, and later reproduce their decision.

### Phase 6 — Build the evaluation dataset and Chapter 3 metric harness

**Tests first**

- Metric calculations for true positives, false positives, true negatives, false negatives, accuracy, precision, recall, and F1.
- Confusion-matrix dimensions and labels are correct for form, stroke, hybrid, and each error type.
- Records with missing expert labels are excluded and reported, not silently counted.
- Writer-level partitions prevent the same writer appearing in tuning and held-out evaluation sets.
- Response-time statistics handle failed requests and missing timing data correctly.
- RAG source-correctness and feedback-relevance records preserve rater identity codes separately from evaluator ratings.

**Implementation**

- Create a versioned evaluation-record schema with fields for: anonymous writer ID, sample ID, target, expert ground truth, individual error labels, form result, stroke result, hybrid result, retrieved sources, feedback rating, and timing.
- Add a backend or offline Python metrics module that emits JSON/CSV tables and confusion-matrix data.
- Keep tuning/calibration records and held-out evaluation records in distinct directories with explicit split metadata.
- Produce a reproducible report input for Chapter 4; Chapter 3 documents the procedure, while actual measured outcomes belong in Chapter 4.

**Done when:** Once expert-labeled data exists, the team can produce the required metrics without redesigning the validator or mixing datasets.

### Phase 7 — Prepare retrieval and feedback evaluation

**Tests first**

- Retrieval selects the target and error-relevant source references only.
- Unsupported error codes and sources cannot enter feedback context.
- Deterministic feedback never adds an error not present in the validator response.
- AI adapter validation rejects invented claims, absent source references, malformed response structures, and timeouts.
- RAG evaluation records store source correctness and feedback relevance ratings separately.

**Implementation**

- Keep deterministic source-grounded feedback as the default.
- Maintain the existing AI-adapter boundary only as an optional explanation layer; it cannot alter validation results.
- Capture retrieval IDs, prompt/model version if used, validation outcome, fallback state, and latency.

**Done when:** The project can evaluate source correctness and feedback relevance as separate Chapter 3 measures.

### Phase 8 — Verification, documentation, and pilot rehearsal

**Tests first**

- End-to-end synthetic fixtures covering valid-like, count-error, order-error, direction-error, trajectory-error, form-error, and kudlit-error paths.
- API tests for invalid samples, missing bundles, mismatched configurations, and unsupported targets.
- Frontend tests for unavailable, provisional, approved, and needs-review display states.

**Implementation and checks**

- Run the backend unit suite, frontend suite, and Next.js production build.
- Rehearse a synthetic `ba` or `ka` flow: capture -> import -> reference bundle -> provisional measurements -> annotation/configuration -> preview -> feedback -> evaluation export.
- Update the README with current limitations, expert collection procedure, configuration location, data retention, and exact test commands.
- Create a manual test checklist for expert collection sessions, including canvas/device conditions and reference-record naming.

**Done when:** The team can demonstrate an honest end-to-end developer workflow and collect expert data consistently.

## 5. Expert-dependent milestones

| Milestone | Can build now? | Requires expert input? |
|---|---:|---:|
| DTW implementation and synthetic tests | Yes | No |
| Image measurements and synthetic tests | Yes | No |
| Response schemas, provenance, and evaluation harness | Yes | No |
| Reference bundle creation | Already available | Yes, for real records |
| Character-specific annotations | UI/schema can be built | Yes, for approval |
| Threshold calibration | Tooling can be built | Yes |
| Learner correctness scoring | No | Yes |
| Accuracy, precision, recall, F1, and confusion matrices | Harness can be built | Yes, labeled held-out data |
| Trained AI/ML classifier | Dataset preparation only | Yes, enough labeled data |

## 6. Collection and calibration protocol to prepare now

Before expert sessions, prepare a short protocol that specifies:

1. the version of the drawing application and canvas size;
2. the target character and source reference used;
3. a consistent stylus/mouse/device note where feasible;
4. multiple independent expert demonstrations per pilot character;
5. an anonymous expert/reviewer code and consent status stored outside the public knowledge graph;
6. a review step that identifies a canonical recording or multiple acceptable templates;
7. annotation of stroke order, direction, count, start/end regions, and kudlit requirements;
8. a separate set of intentionally varied or learner-written samples for threshold tuning;
9. a writer-disjoint, expert-labeled held-out set for final evaluation.

For the first pilot, use a small, expert-approved character set such as `ba` and `ka`, then expand only after the full collection-review-calibration-evaluation cycle works.

## 7. Acceptance criteria

- DTW comparison is deterministic, stroke-aware, resampling-aware, and preserves event order.
- Structural stroke rules, visual form measurements, and hybrid policy remain independently inspectable.
- Every result identifies its source bundle, annotation/configuration, and algorithm versions.
- Synthetic fixtures validate software behavior but are visibly isolated from real reference and evaluation data.
- No developer or learner screen presents a correctness claim without approved expert reference data and matching calibration configuration.
- The developer workflow can collect, replay, visually inspect, annotate, version, and preserve expert data.
- The evaluation harness reports separate form, stroke, hybrid, error-type, retrieval, feedback, and response-time measures against expert-reviewed ground truth.
- Backend and frontend tests are written before each implementation step and pass before the next phase begins.

## 8. Recommended next implementation increment

Begin with **Phase 0 and Phase 1**: versioned algorithm contracts plus a pure, test-driven DTW module using synthetic paths. This work is independent of expert availability, establishes the core stroke algorithm, and does not enable uncalibrated learner scoring.
