# Pinagyamang Baybáyin knowledge graph

This directory is the curated, machine-readable foundation for the validator. It extracts only the parts of Joel Bagain Lopez’s *Pinagyamang Baybáyin: Gabay sa Episyente, Modernisado, at Estandardisadong Pagsulat* that define the writing system, its transformations, and the shared handwriting constraints.

## What is here

- `source-register.json` identifies the supplied primary source and citation format.
- `characters.json` contains the 24 base graphemes, six optional extension symbols, and five source-defined phonetic extensions.
- `diacritics.json` describes vowel replacement, vowel cancellation, repetition, and special marks at a semantic level.
- `orthography-rules.json` contains the source-backed rules that connect those records.
- `graph.json` exposes the same core facts as explicit nodes and edges for graph import.
- `stroke-reference-manifest.json` separates source-level handwriting constraints from the expert-recorded stroke templates the validator still needs.
- `image-references/` contains source-traceable visual pages for the future computer-vision form-validation branch.

## Important scope rule

A record with `status: "source_asserted"` is a fact extracted from the book. It is not automatically a live handwriting-validation threshold. The validator needs approved reference recordings or vector templates for each target symbol before it can score a learner’s strokes.

The graph intentionally stores semantic IDs and source page references instead of reproducing the book’s full charts or artwork. That keeps the data auditable and lets the project attach licensed/reference glyph assets later.

## Source citations

All `sourceRefs` use the PDF page number of the supplied file, not the printed page number inside the book. Use the form `lopez-2025-pdf#pdf-page=N`.

## Current use

The frontend can use this data to select a target, explain its expected sound/state, and display a validation status. The FastAPI service can load it as read-only knowledge data. Do not expose authoring or replacement of these files to ordinary users.
