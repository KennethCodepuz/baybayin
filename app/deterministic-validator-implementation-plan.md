# Implementation plan: deterministic Baybayin validator

**Status:** Historical plan, partly implemented. Active expert bundles support all 12 current targets; local prototype scoring exists for `a`, `ba`, `e`, `i`, `o`, and `u`. The remaining targets and research-grade calibration are still pending. See [CURRENT_SYSTEM_STATUS.md](docs/CURRENT_SYSTEM_STATUS.md).
**Goal:** Turn the existing form-comparison, DTW, and stroke-rule modules into a deterministic, expert-approved validator for learner practice.  
**Decision boundary:** The validator—not an LLM—will decide form, stroke count, order, direction, and kudlit placement. An LLM may later rephrase confirmed results only.

## 1. Why “Check my practice” is unavailable now

The learner endpoint is working safely, but all 12 supplied expert recordings are still **candidate** records. There is currently no:

1. approved character specification;
2. approved reference record and active reference bundle;
3. expert annotation of expected strokes, directions, and mark roles; or
4. approved threshold calibration linked to an active bundle.

The existing modules already produce useful deterministic measurements:

| Component | Existing behavior | Missing decision input |
| --- | --- | --- |
| Form comparison | Normalized PNG mask IoU and ink geometry | Expert-approved form thresholds and error rules |
| Stroke comparison | Stroke count and constrained DTW distance | Expected sequence, accepted distances, and stroke-role annotation |
| Structural rules | Count, direction, start/end-region checks | Approved per-target rules stored and resolved at runtime |
| Feedback | Deterministic messages for confirmed error codes | Confirmed validator output |

The implementation must not infer rules from a single expert JSON simply because it came from an expert. The reviewer must explicitly approve the rules represented by that recording.

## 2. Scope and non-goals

### Included

- A deterministic form, stroke, and hybrid validator for the 12 current targets.
- Separate, inspectable results for form, count, order, direction, trajectory, and kudlit placement.
- Expert annotation, approval, calibration, activation, and audit records.
- Learner-facing deterministic feedback based only on validated findings.
- Evaluation support for Chapter 3.

### Excluded

- LLM or image-model correctness decisions.
- Automatic rule extraction from a book image or one expert example.
- Scoring targets that do not have an active bundle plus matching approved rule and calibration records.
- Database/user-account work; local Git-ignored research records remain sufficient for this phase.

## 3. Core design: three independent deterministic branches

The system will keep the branches separate before producing a hybrid result.

```text
learner JSON (PNG + ordered events)
        |
        +--> form branch: normalized full-image comparison
        |
        +--> stroke branch: count, order, direction, DTW trajectory
        |
        +--> kudlit branch: annotated mark stroke(s), type, and canvas-relative placement
                                      |
                             approved hybrid policy
                                      |
                       deterministic learner result + feedback
```

### Important kudlit rule

The visual grid is not saved and is not itself a validator rule. However, the learner and developer canvases use the same fixed **800×600 coordinate frame**, with the base-character guide at `x=100…700`, `y=100…500`.

For kudlit targets, validation must use the full canvas coordinate frame so an above-grid or below-grid mark remains meaningful. A cropped, normalized whole-image IoU alone is insufficient to explain whether a mark belongs above or below the base character.

The annotation will therefore define, per modified target:

- which recorded stroke(s) are the kudlit/cancellation mark;
- expected mark kind (`dot`, horizontal line, or slanted line);
- expected canvas-relative region(s), such as above or below the base grid;
- expected order relative to base strokes; and
- accepted positional/trajectory tolerances, approved through calibration.

The team must obtain this from reviewer confirmation and replay of the expert recording. Do not infer the mark-stroke index from filename or image pixels.

## 4. Phase 0 — lock the capture frame and pilot scope

### Decision required

Use one capture frame for validation data. The current developer and learner screens use **800×600**; therefore all new expert, calibration, and held-out learner recordings used for deterministic validation must use 800×600. Existing references are already 800×600.

Do not mix 600×450 and 800×600 recordings in calibrated scoring without a separately validated coordinate migration. Both are 4:3, but external-mark placement needs one stable frame.

### Pilot targets

Implement and review in this order:

1. `ba` — base-form and stroke pipeline;
2. `be` and `bo` — line kudlit above/below;
3. `bi` and `bu` — dot kudlit above/below;
4. `b` and `b_` — cancellation line above/below;
5. vowels, then the remaining approved targets.

### Tests first

- Reject a scoring sample whose capture layout does not match the target’s approved validation layout.
- Confirm every pilot recording retains outside-grid coordinates in both PNG and event evidence.

## 5. Phase 1 — approved validator specification and annotation records

### New private local records

Add Git-ignored, immutable JSON records under `app/data/reference-library/`:

| Record | Purpose |
| --- | --- |
| `specification` | Source-backed target description and review decision |
| `stroke-annotation` | Expert-approved structural/kudlit rules tied to one reference bundle |
| `calibration` | Thresholds and hybrid policy tied to that exact bundle and annotation |

Extend the developer library with a review form—not freehand text alone—for the following approved annotation schema:

```json
{
  "schemaVersion": 1,
  "id": "be-strokes-v1",
  "targetId": "be",
  "referenceBundleId": "bundle-...",
  "status": "approved",
  "captureLayout": { "width": 800, "height": 600, "baseGrid": { "left": 100, "top": 100, "right": 700, "bottom": 500 } },
  "expectedStrokeCount": 2,
  "expectedDirections": ["..."],
  "startRegions": [],
  "endRegions": [],
  "mark": {
    "strokeIndices": [1],
    "kind": "horizontal_line",
    "position": "above",
    "regions": [{ "left": 0.40, "top": 0.00, "right": 0.60, "bottom": 0.16 }]
  },
  "approval": { "reviewerCode": "expert-…", "decisionDate": "YYYY-MM-DD", "notes": "…" }
}
```

The numeric sample is schema illustration only. All expected counts, directions, indices, and regions must come from expert review; do not ship example values as live rules.

### Tests first

- An annotation requires target, active bundle, fixed capture layout, reviewer code, date, and status `approved`.
- Each expected stroke has valid normalized start/end regions when used.
- Modified targets require a complete mark section; unmodified targets reject one unless the expert explicitly approves an exception.
- Mark indices are within expected stroke count and are unique.
- Annotation/bundle/target/layout mismatches are rejected.
- Approved annotations are immutable; replacement creates a new version and preserves audit history.

### Done when

An expert can review the replay and save an explicit, auditable deterministic rule set for a pilot target.

## 6. Phase 2 — deterministic structural and kudlit validator

### Reuse and extend existing logic

Keep `stroke_rules.py` as the source for count, direction, start, and end checks. Add a dedicated mark evaluator that receives only:

- structurally valid learner events;
- the approved annotation; and
- the fixed canvas layout.

It must return one or more of these error codes only when the corresponding approved rule fails:

| Condition | Error code |
| --- | --- |
| Missing required mark stroke | `missing_kudlit` |
| Mark stroke is in wrong above/below or horizontal region | `misplaced_kudlit` |
| Dot/line/slanted-line behavior differs from the approved mark kind | `wrong_kudlit_stroke` |
| Extra unannotated mark-like stroke | `unexpected_mark` |
| Count/order fails before mark evaluation | Existing structural error; mark state is `not_evaluated` |

### Mark classification rules

Use transparent geometric features from the selected mark stroke, not machine learning:

- **dot:** small path length and bounded small ink/stroke region;
- **horizontal line:** horizontal direction plus minimum path length;
- **slanted line:** approved directional range plus minimum path length;
- **placement:** stroke center and bounds intersect the annotation’s approved canvas-normalized region.

Thresholds for “small,” “minimum,” and directional tolerance are calibration values. Until approved, return `provisional`, not an error verdict.

### Tests first

- Correct base path plus mark above passes the structural mark placement for `be` only with an approved rule.
- The same mark below produces `misplaced_kudlit`.
- A dot cannot pass a line-kudlit rule and vice versa.
- A mark outside the 4×3 base-grid area is preserved and evaluated, not cropped or discarded.
- Wrong count or order produces a stable result and does not fabricate a kudlit finding.
- Empty, malformed, interrupted, non-finite, or out-of-layout events are rejected safely.

### Done when

The validator can deterministically identify an expert-approved mark location/type error independently of global image similarity.

## 7. Phase 3 — form and trajectory calibration

### Form branch

Continue to calculate normalized mask IoU and centroid/bounds evidence from the full PNG. Add optional approved checks for:

- total ink bounds relative to the 800×600 canvas;
- base-form region occupancy; and
- mark-region ink occupancy, when it strengthens the event-based kudlit result.

This avoids relying exclusively on crop-and-normalize similarity for a mark whose above/below position matters.

### Stroke branch

Use the existing sequence-normalized constrained DTW implementation after structural count/order checks pass. The annotation supplies the expected roles; calibration supplies:

- DTW point count and band ratio;
- maximum normalized path distance per stroke role or target;
- dot-position tolerance; and
- accepted alternative stroke patterns, if the reviewer approves them.

### Calibration dataset and procedure

Collect a private, consented, expert-labeled calibration dataset that is separate from references and held-out evaluation. It must include:

- acceptable learner variation;
- wrong overall form;
- wrong stroke count/order/direction;
- missing, misplaced, and wrong-type kudlit; and
- ambiguous cases labeled as such rather than forced to pass/fail.

For each target, choose thresholds on calibration data only. The expert approves the final values, annotation version, active bundle ID, algorithm versions, and decision date.

### Tests first

- IoU, DTW, dot-position, and mark-placement thresholds require finite approved values in valid ranges.
- A calibration cannot target another bundle, annotation, target, layout, or algorithm version.
- Replacing an active reference bundle makes prior calibration unavailable.
- An uncertain/ambiguous case produces `needs_expert_review`, not a false pass.

### Done when

Each pilot target has a reproducible, approved calibration record capable of turning only its branch measurements into deterministic outcomes.

## 8. Phase 4 — hybrid decision and learner endpoint

### Hybrid policy

Store an approved policy with explicit logic, for example:

```text
form must pass
AND stroke count/order/direction must pass
AND trajectory must pass
AND required kudlit rule must pass
→ hybrid pass
```

The actual policy must be confirmed by the expert and recorded version-by-version. Do not assume every branch has equal authority for every target.

### API behavior

Update `POST /api/learner-validation` only after Phase 3 succeeds:

| Evidence state | Response |
| --- | --- |
| No active bundle | `unavailable` |
| Active bundle, no annotation/calibration | `practice_comparison` with no verdict |
| Complete approved gate | `calibrated_result` with branch and hybrid outcomes |

The endpoint must return only learner-safe structured data: target, result state, confirmed errors, limited deterministic feedback, and source references. It must never return expert samples, raw template images/events, private reviewer data, filesystem paths, tokens, or editable thresholds.

### Deterministic feedback

Map only confirmed error codes to concise guidance. Prioritize in this order:

1. capture/structural problem;
2. stroke count or order;
3. kudlit missing/type/placement;
4. direction/trajectory;
5. form.

Show at most three items, label unavailable/provisional results honestly, and do not use correctness language outside `calibrated_result`.

### Tests first

- Every missing gate returns `unavailable` or `practice_comparison`, never a score.
- A calibrated result reports form, stroke, kudlit, and hybrid outcomes separately.
- Hybrid pass is impossible when a required branch fails or is unavailable.
- The browser cannot select its reference bundle, annotation, calibration, error codes, or thresholds.
- Feedback never invents an error and never includes private expert material.

## 9. Phase 5 — Chapter 3 validation study

Evaluate form, stroke, kudlit, and hybrid validators separately against a writer-disjoint, expert-labeled held-out dataset. Do not tune after observing the held-out results.

Report:

- accuracy, precision, recall, F1-score, and confusion matrices for form, stroke, kudlit, and hybrid results;
- error-specific results for count, order, direction, trajectory, form, missing kudlit, misplaced kudlit, and wrong kudlit type;
- response-time distribution for practical learner feedback;
- calibration/reference/held-out data split and expert-label procedure; and
- deterministic feedback relevance separately from validation accuracy.

If LLM wording is added later, evaluate it separately for feedback relevance and source correctness. It must not alter these validator metrics or decisions.

## 10. Implementation order

1. Confirm 800×600 as the fixed validation capture layout.
2. Review and approve `ba` specification, expert recording, bundle, and structural annotation.
3. Implement rules/annotation repository and developer review UI with tests.
4. Wire count/order/direction and DTW form evidence to the approved `ba` annotation—still provisional.
5. Collect and label `ba` calibration samples; approve its calibration; enable deterministic results for `ba` only.
6. Repeat for `be` and `bo` to validate above/below line-kudlit logic.
7. Repeat for `bi`, `bu`, `b`, and `b_`.
8. Expand only after the pilot’s held-out evaluation is complete.

## 11. Acceptance criteria

- “Check my practice” gives a deterministic verdict only when the exact target has active expert reference, annotation, and calibration records.
- Kudlit marks outside the guide grid are assessed by approved full-canvas stroke/region rules, not lost during image normalization.
- Every form/stroke/kudlit/hybrid result is traceable to a target, bundle, annotation, calibration, algorithm version, and reviewer decision.
- The system handles ambiguous or unsupported evidence safely without inventing a verdict.
- Deterministic feedback is generated solely from confirmed codes; future LLM feedback is explanation-only.
- Chapter 3 can report separate evidence-backed performance for form, stroke, kudlit, and hybrid validation.
