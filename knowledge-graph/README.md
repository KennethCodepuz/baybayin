# Pinagyamang Baybáyin knowledge graph

This directory is the curated, machine-readable foundation for the validator. It extracts only the parts of Joel Bagain Lopez’s *Pinagyamang Baybáyin: Gabay sa Episyente, Modernisado, at Estandardisadong Pagsulat* that define the writing system, its transformations, and the shared handwriting constraints.

## What is here

- `source-register.json` identifies the supplied primary source and citation format.
- The current selectable scope is **A, E, I, O, U, ba, be, bi, bo, bu, b, b_**, in that order. Vowel storage IDs remain lowercase for compatibility. `b` uses the cancellation mark below; `b_` uses it above (workbook PDF pages 15 and 104). The kudlit vowel variants follow the KWF book, PDF page 80.
- `characters.json` defines these 12 `currentReleaseTargets` and retains the source inventory. It contains the 24 base graphemes, six optional extension symbols, and five source-defined phonetic extensions.
- `diacritics.json` describes vowel replacement, vowel cancellation, repetition, and special marks at a semantic level.
- `orthography-rules.json` contains the source-backed rules that connect those records.
- `graph.json` exposes the same core facts as explicit nodes and edges for graph import.
- `stroke-reference-manifest.json` separates source-level handwriting constraints from the expert-recorded stroke templates the validator still needs.
- `image-references/` contains source-traceable visual pages for the future computer-vision form-validation branch.

## Important scope rule

A record with `status: "source_asserted"` is a fact extracted from the book. It is not automatically a handwriting-validation threshold. The application currently has active local expert comparison recordings for the 12 current-release targets, but only `a`, `ba`, `e`, `i`, `o`, and `u` have local prototype form/DTW limits. The remaining targets are comparison-only until accepted calibration samples and reviewed thresholds exist.

The graph intentionally stores semantic IDs and source page references instead of reproducing the book’s full charts or artwork. That keeps the data auditable and lets the project attach licensed/reference glyph assets later.

## Source citations

All `sourceRefs` use the PDF page number of the supplied file, not the printed page number inside the book. Use the form `lopez-2025-pdf#pdf-page=N`.

## Current use

The frontend uses this data to select a target, display a source-backed guide, and retrieve feedback sources. FastAPI loads it as read-only knowledge data. The graph does not decide correctness, store private recordings, or replace expert calibration. Do not expose authoring or replacement of these files to ordinary users.
