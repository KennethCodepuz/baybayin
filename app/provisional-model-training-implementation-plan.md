# Implementation plan: provisional hybrid model training

**Status:** Feature extraction, writer-disjoint training, and preliminary evaluation implemented.  
**Purpose:** Train and demonstrate a preliminary Baybayin conformity classifier from the collected group dataset, while preserving a clean path to expert-reviewed research validation next semester.  
**Method:** Test-driven development. Write each pipeline test with a synthetic or non-sensitive fixture first, then make the smallest implementation that passes it.

## 1. Research boundary and current data

This is proof-of-concept model development, not final expert-ground-truth evaluation.

- `expert reference/` holds 12 immutable expert-created canonical recordings. They define reference-relative features; they never become learner training or held-out test examples.
- `dataset/W01`, `dataset/W02`, and `dataset/W03` hold 162 group-protocol recordings.
- All 162 current records pass the version-1 FastAPI sample schema, use 800×600 canvases, and have no exact duplicate files.

| Target group | Targets | Conditions per writer | Samples per target |
|---|---|---:|---:|
| Plain | `a`, `e`, `i`, `o`, `u`, `ba` | conforming, wrong form, wrong count, wrong process | 12 |
| Modified | `be`, `bi`, `bo`, `bu`, `b`, `b_` | conforming, wrong form, wrong count, wrong process, wrong kudlit | 15 |

The binary labels are currently 36 intended-conforming and 126 controlled non-conforming samples. Use training-only class weighting and balanced metrics. Adding two more conforming attempts per writer and target later is recommended, but not required for the first run.

This phase may claim only that a trained model distinguishes group-protocol intended-conforming and controlled non-conforming attempts. It must not claim expert validation, population generalization, or final thesis performance.

## 2. Fixed model definition

```text
group JSON sample + matching expert reference
  -> normalized image and stroke features
  -> deterministic baseline and trained classifier
  -> conforming / non_conforming
```

Each derived feature row must contain target ID, writer code, image-form measurements (IoU, centroid distance, ink bounds), stroke measurements (count difference, constrained DTW, dot position, path-length ratio, start/end displacement), process indicators, and kudlit/cancellation-mark features where applicable. Preserve raw JSON unchanged.

Compare two methods:

1. A deterministic baseline using fold-specific thresholds/rules fitted from training writers only.
2. A weighted Random Forest with training-only class weighting using the same feature rows.

Random Forest is the initial candidate because the dataset is small and features are mixed and interpretable. Do not add a deep neural network in this pilot.

## 3. Phase 1 — manifest and provisional labels

Create a Git-ignored manifest outside raw recordings with: `sampleId`, relative path, checksum, writer code, target, round, canvas, condition, binary label, label source, review status, and quality status.

Normalize filenames and labels:

| Existing name | Normalized condition | Binary label |
|---|---|---|
| `conformed` | `intended_conforming` | `conforming` |
| `wrong-form` | `wrong_form` | `non_conforming` |
| `wrong-count` | `wrong_count` | `non_conforming` |
| `wrong-kudlit` | `wrong_kudlit` | `non_conforming` |
| `wrong-direction` | `wrong_process`, subtype `wrong_direction` | `non_conforming` |
| `wrong-process` | `wrong_process`, subtype `unspecified` | `non_conforming` |

Set all group rows to `labelSource=group_protocol` and `reviewStatus=provisional`. Do not infer whether generic `wrong-process` means direction or order; ask its writer later. Store expert references in a separate canonical-reference manifest with `labelSource=expert_reference` and `usage=canonical_reference`.

### Tests first

- Every manifest path stays inside the intended dataset directory.
- Every raw file passes the existing `Sample` schema before it receives a manifest row.
- Folder target, JSON target, and manifest target must match.
- Duplicate checksums and unknown conditions fail.
- Generic `wrong_process` never becomes direction or order automatically.

## 4. Phase 2 — cleaning and feature table

1. Never overwrite raw JSON or expert references.
2. Exclude malformed, incomplete, duplicate, empty-ink, or accidental multi-error samples while preserving an exclusion reason in the manifest.
3. Store normalized images, derived stroke features, and feature rows separately from raw recordings.
4. Calculate every feature relative to the matching expert record using one preprocessing/feature-schema version.

### Tests first

- Excluded samples cannot enter the training table.
- Every feature row retains sample ID, writer, target, reference checksum, and feature-schema version.
- Missing expert references fail clearly.
- Intended translation/scale invariance remains stable.

## 5. Phase 3 — writer-separated training

Use leave-one-writer-out cross-validation:

```text
Fold 1: train W01 + W02; test W03
Fold 2: train W01 + W03; test W02
Fold 3: train W02 + W03; test W01
```

For every fold:

1. Fit baseline thresholds, preprocessing, feature selection, and class weighting from training writers only.
2. Train the weighted Random Forest from training feature rows only.
3. Predict every held-out writer sample with both methods.
4. Save seed, model version, training writers, feature schema, reference-manifest version, and output checksum.

### Tests first

- A held-out writer is absent from every fitting and training call.
- A fixed seed gives reproducible fixture results.
- Non-finite or missing features fail instead of silently converting.
- Both methods predict for a complete valid feature row.

## 6. Phase 4 — pilot evaluation

Calculate only from out-of-fold predictions:

- confusion matrix;
- accuracy and balanced accuracy;
- precision, recall, and F1 for `non_conforming`;
- per-writer results;
- descriptive per-target results; and
- deterministic-baseline versus Random Forest comparison.

Do not report direction/order error-classifier metrics for generic `wrong_process` samples. State the writer count, class distribution, seed, feature schema, and provisional-label limitation in every report.

### Tests first

- Evaluation accepts only out-of-fold predictions.
- Zero-denominator metrics are explicit, not silent success.
- Expert references never appear in training predictions or evaluation rows.

## 7. Phase 5 — developer testing view

After offline evaluation passes, add a developer-only test view that accepts a checked drawing, computes the frozen feature schema against its expert reference, and shows deterministic-baseline and trained-model results separately. Every result must say **preliminary group-protocol model result**. Do not replace learner-facing validation with this model until a future expert-review decision.

## 8. Deliverables

- Git-ignored manifests and data dictionary;
- reproducible feature-extraction, training, and evaluation scripts;
- baseline and trained-model artifacts with run metadata;
- pilot report with writer-separated results and limitations; and
- developer-only testing view.

## 9. Deferred to next semester

1. Expert review/correction of provisional labels.
2. Formal per-target order, direction, and kudlit rules.
3. More writers and balanced conforming attempts.
4. Frozen expert-labeled final test set and final Chapter 3/4 performance claims.
