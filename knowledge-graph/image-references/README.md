# Image reference layer

This directory holds only the PDF pages needed to establish visual form references for the image-based branch of the hybrid validator. Every asset is traceable to the supplied Lopez (2025) PDF through `manifest.json`.

## Contents

- `source-pages/` contains rendered pages for the core-character chart, kudlit-pamalit placement, Grid-Baybáyin guidance, and character-form practice pages.
- `manifest.json` links each asset to source pages and records its role.

## Important boundary

These pages are authoritative visual source material, but they are **not** automatic ground-truth templates or thresholds for computer-vision scoring. The local application currently compares learner images with active expert-recording bundles; the source pages remain guide/provenance material. Only `a`, `ba`, `e`, `i`, `o`, and `u` have local prototype image/DTW limits. Every remaining target still needs accepted calibration data and reviewed tolerances before it can receive a score.

Future per-character files should use this structure:

```text
canonical/<target-id>.png
annotations/<target-id>.json
```

An annotation should describe the normalized glyph bounds, Grid-Baybáyin landmarks, permitted kudlit region, and the approved template/version it supports. Do not put private reviewer details or unapproved participant drawings in this source-reference directory.
