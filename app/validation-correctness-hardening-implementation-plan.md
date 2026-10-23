# Implementation plan: validation-correctness hardening

**Status:** Proposed; this document makes no code changes.  
**Goal:** Fix the five issues that must be resolved before expert recordings are collected or any learner pass/fail scoring can be enabled.  
**Method:** Test-driven development. For each behavior, add a focused test that fails for the identified defect, implement the smallest fix, run the relevant test group, then run the complete backend and frontend checks at the end.

## 1. Scope and safeguards

This plan fixes:

1. zero-length dot strokes that currently fail DTW comparison;
2. malformed or oversized PNG input that can fail preview processing or consume too many resources;
3. arbitrary or obsolete reference-bundle selection when more than one expert bundle exists for a target;
4. structural rules that are accepted without explicit expert approval metadata; and
5. stroke scoring that can pass with no actual DTW comparison.

It does not:

- establish Baybayin thresholds;
- make a learner-facing correctness claim;
- alter the committed knowledge graph source facts;
- add authentication, a database, or deployment;
- convert synthetic test data into expert ground truth.

All changes must retain this invariant:

> A form, stroke, or hybrid pass/fail result is impossible unless there is a matching approved expert reference bundle and a matching approved calibration configuration.

## 2. Phase 1 — Support stationary dot strokes

### Problem

The capture schema accepts a valid `down -> up` stroke whose start and end coordinates are equal. The feature extractor classifies it as `stationary`, but `normalize_stroke_sequence()` rejects it because its path length is zero. A dot kudlit can therefore cause DTW evidence generation to fail.

### Tests first

Add tests that prove:

- a standalone two-event stationary stroke is represented as a dot rather than rejected;
- a glyph containing a normal path plus one dot can be normalized and compared;
- matching reference and learner dots produce deterministic dot-position evidence;
- displaced dots produce a measurable dot-position distance;
- a dot is not passed through arc-length resampling or regular DTW;
- malformed one-event strokes and non-finite coordinates remain rejected;
- the bundle-to-preview path accepts a sample containing a dot and returns pending evidence, never a server error.

### Implementation

1. Extend stroke feature data with an explicit geometry type such as `path` or `dot`.
2. Preserve original recorded events and existing stroke order.
3. Normalize dot coordinates with the glyph’s shared bounds.
4. Compare matching dot strokes by normalized center-point distance; compare path strokes with constrained DTW.
5. Return evidence that identifies whether each comparison was `dot_position` or `dtw_path`.
6. Retain `wrong_stroke_count` behavior before any per-stroke comparison.

### Done when

A valid stationary kudlit can be captured, bundled, replayed, and included in provisional DTW evidence without an exception or a correctness score.

## 3. Phase 2 — Validate image bytes and impose safe image limits

### Problem

The API currently validates the data-URL prefix and Base64 shape but does not verify actual PNG bytes during sample checking. Image decoding happens later during bundle creation or preview. A malformed PNG therefore reaches image processing, and a compressed image with extreme dimensions can consume excessive memory.

### Tests first

Add API/model and pure-image tests that prove:

- valid PNG data passes structural sample checking;
- Base64 that is not a real PNG is rejected with a clear `422` response;
- blank images remain valid captures but are rejected only where visible ink is required for a bundle or form measurement;
- images above the selected maximum width, height, pixel count, or decoded byte limit are rejected before full pixel loading;
- a decompression-bomb warning/error becomes a controlled validation error;
- malformed image input in `/api/validation/preview` returns `422`, not `500`;
- a preview failure leaves stored reference records and bundles unchanged.

### Implementation

1. Define named limits for encoded payload size, decoded byte size, width, height, and total pixels. Document their rationale in the README.
2. Add a single shared PNG decoder/validator in `multimodal.py`.
3. Open the image, inspect format and dimensions before calling `load()`, then reject oversized data.
4. Reuse the decoder in sample validation, image normalization, reference-bundle creation, and form matching.
5. Map expected image and stroke processing failures to `HTTP 422 Unprocessable Content` at API boundaries.
6. Do not put raw image bytes or decoded images in error messages or logs.

### Done when

Every accepted sample has verified, bounded PNG data, and invalid images cannot crash the preview route or allocate unbounded image memory.

## 4. Phase 3 — Select one explicit active reference bundle

### Problem

Preview currently selects the first bundle with a matching target ID. Once a target has several approved recordings or a record is superseded, this can select an arbitrary or obsolete reference.

### Tests first

Add repository and API tests that prove:

- a target with no active bundle returns `reference_bundle_missing`;
- exactly one active approved bundle resolves successfully;
- a superseded record’s bundle cannot be selected;
- an inactive bundle cannot be selected;
- two active bundles for one target produce a controlled `needs_expert_review`/ambiguous state, never arbitrary selection;
- a new approved bundle can become active only through an explicit review action;
- an active-bundle transition preserves prior bundle files and audit history;
- readiness distinguishes “approved reference exists” from “an active validation bundle exists.”

### Implementation

1. Add bundle lifecycle metadata: `status` (`candidate`, `approved`, `active`, `superseded`), `activatedBy`, `activatedAt`, and a version/reason field.
2. Keep bundle contents immutable. Activation changes a separate target-to-active-bundle registry or creates a new review record; it never rewrites the expert source sample.
3. Add repository helpers to resolve the sole active bundle for a canonical target ID.
4. Update preview to resolve the canonical graph target ID first, then use only that active bundle.
5. Return a safe unavailable/needs-review branch result for missing or ambiguous selection.
6. Update the developer reference-library interface to display bundle state and offer an explicit activation action only for approved expert bundles.

### Done when

Every preview identifies one deliberate active bundle, or clearly reports that expert review is required. It never chooses a bundle by incidental file ordering.

## 5. Phase 4 — Require explicit structural-rule approval

### Problem

`evaluate_structural_strokes()` accepts a rule dictionary with no `status` field, even though structural findings must be tied to an approved expert annotation.

### Tests first

Add tests that prove:

- missing `status` is rejected;
- `draft`, `candidate`, and `superseded` annotations are rejected;
- only `approved` annotations with reviewer code, decision date, version, target ID, and matching bundle ID are accepted;
- invalid normalized regions, invalid direction labels, duplicate stroke indices, and mismatched stroke counts are rejected;
- a valid approved annotation produces deterministic structural evidence containing its approval/version provenance;
- preview remains unavailable when a bundle exists but no approved structural annotation exists.

### Implementation

1. Define a versioned structural-annotation schema.
2. Require fields for target ID, reference bundle ID, status, reviewer code, decision date, annotation version, expected stroke count, and optional approved regions/directions.
3. Make `status == "approved"` mandatory; do not use a default.
4. Validate that the annotation belongs to the same canonical target and active bundle being evaluated.
5. Return annotation ID/version and approved source references in structural evidence.
6. Keep annotation files immutable after approval; corrections create a new version.

### Done when

Every structural error can be traced to a specific approved expert annotation rather than developer-supplied defaults.

## 6. Phase 5 — Prevent empty DTW evidence from passing

### Problem

`score_stroke_measurements()` treats an empty comparison list and no structural errors as a successful score. A future integration error could therefore produce a false pass without comparing a stroke.

### Tests first

Add tests that prove:

- empty comparisons with no structural errors are rejected or returned as `needs_review`, never passed;
- expected path strokes require one DTW comparison for each matched path stroke;
- expected dot strokes require one dot-position comparison for each matched dot stroke;
- duplicate, skipped, or out-of-range stroke indices are rejected;
- comparison algorithm versions must match the approved calibration configuration;
- non-finite, negative, or absent distances are rejected;
- structural errors remain visible and cannot be overwritten by scoring;
- form scoring similarly rejects non-finite or out-of-range IoU values.

### Implementation

1. Include expected comparison count and geometry types in the approved structural annotation or bundle-derived feature metadata.
2. Validate the complete evidence set before threshold evaluation.
3. Return `available: false`, `passed: null`, and `missing_comparison_evidence` when measurements are incomplete.
4. Calculate a stroke pass/fail only after complete structural and trajectory evidence is present and the approved configuration matches target and active bundle.
5. Add `math.isfinite()` checks to all calibration values and received measurement values.

### Done when

No missing, empty, malformed, or mismatched DTW evidence can produce a stroke pass.

## 7. Cross-cutting integration and migration

1. Introduce data-schema versions for bundles, structural annotations, and active-bundle registry records.
2. Treat existing local bundles as legacy records. Do not silently activate them.
3. Provide a developer-only migration/check command that lists legacy bundles requiring explicit expert review; it must not change data automatically.
4. Preserve Git-ignore rules for local expert recordings, bundles, reviewer details, and private manifests.
5. Update the README and developer interface wording so provisional evidence, approved reference, active reference, and calibrated scorer are visibly distinct.

## 8. Verification checklist

Run after every phase and again at completion:

```powershell
# From app\backend
.\.venv\Scripts\python.exe -m pytest -q
.\.venv\Scripts\python.exe -m py_compile main.py multimodal.py reference_library.py reference_bundle.py stroke_matching.py stroke_rules.py form_matching.py validation_config.py scoring.py validation_evidence.py

# From app\frontend
npm.cmd test
npm.cmd run build
```

Perform these manual developer checks with synthetic data only:

1. Import a valid path-only sample and create a candidate reference.
2. Import a sample containing a stationary dot and confirm replay, bundle creation, and preview evidence work.
3. Attempt to import malformed, blank, and oversized PNG data; confirm controlled errors and no saved record.
4. Create multiple bundle versions for one target; confirm no preview runs until one is explicitly active.
5. Attempt to score missing comparison evidence; confirm the response remains unavailable.
6. Confirm no screen reports a learner as correct or incorrect without approved expert annotations and calibration.

## 9. Acceptance criteria

- Dot strokes are supported as first-class stroke evidence.
- Image inputs are decoded, bounded, and safely rejected when malformed or oversized.
- Preview uses exactly one explicitly active, non-superseded bundle.
- Structural rules require complete, matching expert-approval provenance.
- Incomplete DTW evidence cannot yield a pass.
- Existing reference data remains immutable; activation and corrections are auditable new records.
- Backend/API, frontend, and production-build checks pass.
- The system continues to state that scoring is unavailable until real expert approval and calibration exist.

## 10. Recommended order

Implement in this order:

1. Image safety (Phase 2), because it protects every subsequent import and preview operation.
2. Dot-stroke support (Phase 1), because it prevents legitimate expert samples from failing.
3. Active-bundle lifecycle (Phase 3), before any real bundle is used for comparison.
4. Structural-annotation approval (Phase 4).
5. Complete-evidence scoring checks (Phase 5).

This order makes the collection workflow safe before the team begins storing professional expert recordings.
