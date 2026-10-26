# Implementation plan: expert-reference import and activation

**Status:** Historical plan, implemented for the declared local batch. The recordings were imported, reviewed locally, and activated for comparison; learner scoring coverage is in [CURRENT_SYSTEM_STATUS.md](docs/CURRENT_SYSTEM_STATUS.md).
**Goal:** Import the 12 recordings in `expert reference/` into the protected developer reference library, preserve their expert provenance, and activate only explicitly reviewed reference bundles for future learner validation.  
**Method:** Test-driven development. Add failing tests before each behavior, implement the smallest change, then run focused checks before the full project checks.

## 1. What this batch contains

The supplied batch contains 12 structurally valid JSON recordings from the identified expert:

| Group | Targets | Files |
| --- | --- | --- |
| Vowels | `a`, `e`, `i`, `o`, `u` | `expert_.A.json` through `expert_.U.json` |
| `b` family | `ba`, `be`, `bi`, `bo`, `bu`, `b`, `b_` | `expert_b*.json` |

Each recording contains both required modalities:

- a final 800×600 PNG image; and
- ordered mouse stroke events.

All 12 target IDs are eligible in the current knowledge graph. The 800×600 canvas is 4:3, matching the new 600×450 collection layout proportionally. Existing recordings remain immutable; new data collection should use 600×450.

## 2. Scope and safeguards

This plan will:

1. preserve the original expert files without modifying their JSON, PNG data, events, timestamps, or canvas dimensions;
2. import copies as candidate records in `app/data/reference-library/`;
3. attach source, capture, expert-review, and import provenance;
4. create matching approved specifications and immutable multimodal bundles;
5. require explicit reviewer confirmation before a bundle becomes active; and
6. make preview use the activated expert bundles for provisional learner measurements.

This plan will not:

- enable learner pass/fail scoring or invent DTW/image thresholds;
- treat an uploaded filename as proof of expert identity;
- overwrite, normalize in place, or delete any source recording;
- expose private expert records through public endpoints; or
- import targets beyond the supplied batch.

The source JSON becomes a **candidate expert recording** on import. It becomes an active validation reference only after the assigned reviewer confirms the source, target, and specification in the developer review interface.

## 3. Phase 1 — Batch manifest and provenance record

### Problem

The existing developer page imports one recording at a time and has no durable record linking an imported reference back to its original expert batch file.

### Tests first

Add tests proving that:

- a batch manifest accepts only the 12 expected file names and target IDs;
- each manifest entry contains source file name, SHA-256 checksum, target ID, expert code, source document references, capture method, and collection date;
- a checksum mismatch, missing file, duplicate target/file entry, unknown target, or an invalid filename stops the batch before any record is saved;
- the original source JSON is read-only during import; and
- the manifest itself contains no unnecessary personal data.

### Implementation

1. Add `app/research/expert-reference-batch-2026-10-24.json` as a reviewed manifest, not as validator input.
2. Record one entry per supplied file with its known target and the file checksum calculated from the original JSON bytes.
3. Use a non-identifying expert code, the agreed source references from the knowledge graph, capture method `mouse`, source canvas `800×600`, and collection date `2026-10-24`.
4. Add an import summary field listing included targets and the deferred targets not yet supplied.
5. Keep the raw source recordings in the private `expert reference/` directory or approved private storage; do not add them to Git unless consent and data policy explicitly permit it.

### Done when

The team can prove which original expert file produced every imported library record without exposing private data publicly.

## 4. Phase 2 — Safe batch preflight and candidate import

### Tests first

Add tests proving that:

- preflight validates every file with the same `Sample` schema used by the API;
- all files must pass before any library write occurs;
- importing a valid batch creates one candidate record per manifest entry;
- each candidate retains its exact source sample, including 800×600 dimensions and ordered events;
- importing the same batch twice reports stable duplicates rather than creating new records;
- an unknown, malformed, checksum-mismatched, or out-of-release recording causes a clear per-file result and does not partially activate anything; and
- the local reference token is required for batch import.

### Implementation

1. Add a protected developer-only batch-import command or endpoint. It receives a manifest path and reads only files under the designated private expert-reference root.
2. Validate filename, resolved path containment, checksum, target match, PNG safety, event order, coordinate bounds, and graph eligibility before creating a record.
3. Import each valid recording through the existing `ReferenceRepository.create_record()` path so checksum deduplication, atomic writes, and manifest updates remain central.
4. Store import provenance with batch ID, original filename, original-file SHA-256, imported timestamp, capture layout, and the importer’s authorized identity.
5. Return a review report with imported, duplicate, blocked, and missing-target entries. Never activate a bundle during import.

### Done when

The 12 source files can be reproducibly imported as protected candidate records with no source-file mutation and no partial trusted state.

## 5. Phase 3 — Reviewer confirmation and character specifications

### Tests first

Add tests proving that:

- a candidate cannot be approved without a matching approved specification for the same target;
- reviewer confirmation requires the authenticated reviewer role plus an explicit reviewer code, decision date, notes, and batch ID;
- the reviewer sees the original PNG, replayed strokes, target, source references, canvas size, stroke count, and provenance before approving;
- approved specifications correctly identify the base form and the mark form/position for `be`, `bi`, `bo`, `bu`, `b`, and `b_`;
- a reviewer cannot approve a file for a different target; and
- rejection/supersession preserves the candidate and its review history.

### Implementation

1. Add a review queue filtered by `batchId` to the Developer Reference Library.
2. Display the source recording and an explicit immutable provenance panel before review actions.
3. Create versioned character specifications from the knowledge graph. For the `b` family, include the source-backed kudlit form and position already represented by the target metadata.
4. Keep reviewer confirmation as an explicit action; do not auto-approve from the batch manifest.
5. Record the review decision as a new audit entry rather than changing source-capture facts.

### Done when

Each approved expert reference has a matching expert-reviewed specification and a visible, auditable decision trail.

## 6. Phase 4 — Bundle creation, activation, and learner-preview eligibility

### Tests first

Add tests proving that:

- one approved record plus its matching approved specification creates an immutable expert bundle;
- a bundle retains normalized image evidence and extracted stroke features while preserving a link to the original source sample;
- an inactive, rejected, superseded, or wrong-target bundle cannot be resolved by learner preview;
- an authorized reviewer can explicitly activate one approved bundle per target;
- activating a replacement preserves the former activation in history; and
- `/api/validation/preview` uses only the active expert bundle and returns provisional measurements with no correctness score.

### Implementation

1. Create bundles from each approved imported record through the existing immutable bundle builder.
2. Add batch status indicators: `candidate`, `specification approved`, `bundle created`, `active`, and `missing`.
3. Activate only reviewer-confirmed bundles. The active-bundle registry remains the sole route used by preview.
4. Return source references, bundle ID, and provisional image/stroke measurements for developer inspection, but keep `passed: null` until calibration is completed.

### Done when

The validator can compare a learner’s `ba` or other supplied target against the explicitly activated expert recording, while still refusing pass/fail decisions.

## 7. Phase 5 — Dataset coverage and collection follow-up

### Current coverage

The batch covers 12 targets. It does not yet cover the remaining current-release targets, including the non-`b` consonant families.

### Tasks

1. Produce a coverage report that distinguishes active expert references, approved-but-inactive references, candidates awaiting review, and missing targets.
2. Schedule the next expert collection using the standard 600×450 canvas and 4×3 visual grid.
3. Collect more than one approved reference per target where possible, especially before calibration and final evaluation.
4. Keep expert references separate from learner samples and held-out evaluation samples.
5. Do not set DTW or form thresholds until expert-labeled learner data exists.

## 8. Verification

Run after each phase and again at completion:

```powershell
# From app\backend
.\.venv\Scripts\python.exe -m pytest -q --basetemp .tmp\pytest
.\.venv\Scripts\python.exe -m py_compile main.py reference_library.py reference_bundle.py validation_evidence.py

# From app\frontend
npm.cmd test
npm.cmd run build
```

Manual developer checks with the private expert batch:

1. Run batch preflight; confirm all 12 checksums, targets, PNGs, and event sequences pass.
2. Confirm no source file is changed after preflight or import.
3. Confirm unauthenticated requests cannot import, list, download, approve, bundle, or activate expert material.
4. Review one candidate, approve a matching specification, create a bundle, and activate it.
5. Submit a synthetic learner recording for that target and confirm preview identifies the active expert bundle but reports only provisional measurements.
6. Confirm no learner result says correct or incorrect until an approved calibration configuration exists.

## 9. Acceptance criteria

- All 12 supplied recordings are validated, checksum-linked, and imported as private candidate records.
- Every activated reference is traceable to its original expert file, source facts, specification version, reviewer decision, and bundle ID.
- The active bundle is the only source used for learner preview for its target.
- The system never silently selects, overwrites, or auto-approves an expert recording.
- Missing targets remain clearly reported and cannot receive a false validation result.
- No learner pass/fail scoring is enabled by this import alone.
