# Image reference layer

This directory holds only the PDF pages needed to establish visual form references for the image-based branch of the hybrid validator. Every asset is traceable to the supplied Lopez (2025) PDF through `manifest.json`.

## Contents

- `source-pages/` contains rendered pages for the core-character chart, kudlit-pamalit placement, Grid-Baybáyin guidance, and character-form practice pages.
- `manifest.json` links each asset to source pages and records its role.

## Important boundary

These pages are authoritative visual source material, but they are **not** automatic ground-truth templates for computer-vision scoring. For each target, the project still needs an expert-approved character specification, a linked approved JSON stroke recording, a canonical image rendered from that recording, and reviewed image annotations/tolerances.

Future per-character files should use this structure:

```text
canonical/<target-id>.png
annotations/<target-id>.json
```

An annotation should describe the normalized glyph bounds, Grid-Baybáyin landmarks, permitted kudlit region, and the approved template/version it supports. Do not put private reviewer details or unapproved participant drawings in this source-reference directory.