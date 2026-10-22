# Implementation plan: multimodal Baybayin validator infrastructure

**Status:** Proposed; this document does not implement the validator.  
**Goal:** Build the infrastructure for separate image-based form validation, JSON-based stroke validation, a hybrid decision, and source-grounded AI feedback. The system must remain unable to claim learner correctness until approved expert references and evaluation data are available.  
**Method:** Test-driven development. Write each test before its implementation, verify it fails for the intended reason, implement the smallest change, and rerun the relevant suite.

## 1. Starting point

The project currently captures an intended target, an ordered JSON stroke sequence, and a final PNG image in one sample. FastAPI structurally checks the sample. The developer reference library keeps candidate and approved recordings distinct, and the root knowledge graph now has text rules plus source-traceable visual reference pages.

An expert who draws inside the developer interface will therefore create both input modalities at once:

```text
expert drawing in browser
  -> ordered pointer-event JSON for stroke analysis
  -> final PNG for image-form analysis
  -> candidate record
  -> expert-approved specification and reference record
  -> linked canonical stroke and image templates
```

The professional book pages are visual source references. They are not by themselves learner-scoring thresholds or approved stroke templates.

## 2. Scope

This phase delivers infrastructure, schemas, deterministic baseline feature extraction, error contracts, and a grounded-feedback boundary.

It includes:

1. Versioned multimodal reference-template records linked to approved expert recordings.
2. Image normalization and visual annotation support for a future computer-vision form validator.
3. JSON stroke segmentation and feature extraction for a future online-handwriting validator.
4. A common error taxonomy and hybrid decision contract.
5. A source-retrieval boundary and AI-feedback request/response contract.
6. Test fixtures, audit metadata, and developer documentation.

It does not include:

- final production scoring thresholds;
- a claim of learner correctness or measured accuracy;
- training a machine-learning model without labeled expert data;
- public uploads, authentication, a database, or deployment;
- direct modification of source rules through the browser;
- generated feedback that can override a validator result.

## 3. Multimodal data model

### 3.1 Approved reference bundle

Create one immutable, versioned `referenceBundle` only after both of these exist:

- an approved reference-library recording; and
- a matching approved character specification.

Each bundle should contain:

```json
{
  "id": "bundle-consonant-ka-v1",
  "targetId": "ka",
  "referenceRecordId": "ref-...",
  "specificationVersion": "ka-1.0",
  "sourceRefs": ["lopez-2025-pdf#pdf-page=56"],
  "image": {
    "originalSampleImage": "reference to immutable sample image",
    "canonicalImagePath": "generated/ka/canonical-v1.png",
    "normalizedWidth": 256,
    "normalizedHeight": 256,
    "annotationPath": "annotations/ka-v1.json",
    "approvedBy": "expert-code",
    "approvedAt": "YYYY-MM-DD"
  },
  "stroke": {
    "sourceSampleId": "ref-...",
    "strokeCount": 0,
    "orderedStrokeIds": [],
    "featureSchemaVersion": 1
  },
  "status": "approved"
}
```

Keep the original sample unchanged. Derived images, normalized points, annotations, and features must preserve the source-record ID and schema version.

### 3.2 Image annotations

An annotation file must use normalized coordinates from `0` to `1` and include:

- overall glyph bounding box;
- Grid-Baybáyin dimensions and relevant axis/landmark positions;
- required visual regions or curves;
- permitted ink area;
- optional or required kudlit region;
- expected connected-component count where expert-approved;
- source reference, reviewer, specification version, and decision date.

Do not infer visual tolerances from a PDF page alone. An expert must approve them.

### 3.3 Stroke features

Derive, but do not overwrite, these features from the ordered JSON events:

- stroke count and pen-lift boundaries;
- normalized points per stroke;
- start and end positions;
- direction vector and direction changes;
- path length and bounding box;
- relative placement of strokes and kudlit;
- event duration when the study decides it is relevant.

A feature record must retain enough information to reproduce its result from the original sample.

## 4. Error taxonomy and decision contract

Use machine-readable codes. Keep user-facing wording outside the validation algorithm.

### 4.1 Form errors

- `wrong_form`
- `missing_required_region`
- `unexpected_mark`
- `out_of_bounds_proportion`
- `missing_kudlit`
- `misplaced_kudlit`
- `ambiguous_form`

### 4.2 Stroke errors

- `wrong_stroke_count`
- `wrong_stroke_order`
- `wrong_stroke_direction`
- `wrong_start_region`
- `wrong_end_region`
- `trajectory_mismatch`
- `wrong_kudlit_stroke`

### 4.3 Hybrid response

The form and stroke branches must remain independently inspectable. The hybrid layer combines their outputs through a documented policy; it must not hide a branch failure.

```json
{
  "schemaVersion": 1,
  "targetId": "ka",
  "referenceBundleId": "bundle-consonant-ka-v1",
  "form": {
    "available": false,
    "passed": null,
    "errors": [],
    "evidence": []
  },
  "stroke": {
    "available": false,
    "passed": null,
    "errors": [],
    "evidence": []
  },
  "overall": {
    "available": false,
    "passed": null,
    "policyVersion": "pending-expert-thresholds"
  },
  "sourceRefs": []
}
```

Until an approved bundle and validation thresholds exist, `available` must be `false` and `passed` must be `null`; never return a fabricated pass/fail score.

## 5. Grounded AI feedback contract

The AI is an explanation layer. It does not inspect raw samples as the deciding authority and cannot change `form`, `stroke`, or `overall` outcomes.

### Input to retrieval and AI

Provide only:

- target ID and source-supported name;
- structured validator error codes and evidence summaries;
- approved source references and image-reference IDs;
- learner language preference, if supported;
- an explicit statement that the explanation may not infer extra errors.

### Retrieval behavior

1. Retrieve the character node, relevant kudlit/rule nodes, related visual source asset, and the precise source references.
2. Prefer the smallest sufficient source set.
3. Return a no-feedback/needs-review state when no approved source applies.
4. Record the retrieved IDs, model/prompt version, and response time for later RAG evaluation.

### AI output

Require structured output with:

- concise learner-facing explanation;
- detected mistake(s), using only supplied error codes;
- corrective action;
- source references used;
- uncertainty/needs-review flag when applicable.

Provide deterministic template feedback as a fallback whenever the AI service is unavailable or returns unsupported claims.

## 6. TDD implementation sequence

### Step 1 — Define and validate multimodal schemas

1. Add backend tests for valid and invalid reference bundles, annotations, normalized coordinates, source references, schema versions, and immutable reference-record links.
2. Add synthetic `ba` and `ka` bundles and deliberately invalid fixtures. Mark every fixture as test data.
3. Implement Pydantic models and a local repository only after the tests fail.
4. Reject bundle creation when the referenced record or specification is missing, non-approved, mismatched, or superseded.

**Done when:** A future validator can resolve an approved bundle without treating source pages or test fixtures as ground truth.

### Step 2 — Build deterministic image preprocessing

1. Write tests for transparent/white background handling, ink bounding-box detection, padding, aspect-ratio preservation, grayscale/binary output, deterministic output dimensions, and an empty-canvas error.
2. Implement a pure preprocessing module that takes the sample PNG and produces a normalized image plus provenance metadata.
3. Save generated artifacts outside the source-reference directory and outside tracked files. Preserve the original image in the source sample.
4. Add visual regression fixtures only for synthetic data or expert-approved assets.

**Done when:** The same image always produces the same normalized image and metadata, without assigning a correctness score.

### Step 3 — Build deterministic stroke segmentation and features

1. Write tests for dots, one-stroke forms, multiple strokes, pen lifts, malformed event sequences, coordinate normalization, start/end regions, path length, direction vectors, and kudlit separation.
2. Implement a pure feature extractor operating on the existing ordered-event schema.
3. Persist derived feature data with a schema version and checksum of its source sample.
4. Verify that no feature extractor mutates or reorders the original events.

**Done when:** Every captured sample can produce reproducible image and stroke features, independently of a scoring model.

### Step 4 — Implement form and stroke baseline interfaces

1. Write tests for form-validator and stroke-validator responses with unavailable references, pending bundles, valid synthetic comparison inputs, multiple error codes, and no false pass/fail before thresholds are approved.
2. Implement interfaces that return the common branch response shape: availability, pass state, error codes, evidence, reference-bundle ID, and source references.
3. Implement only non-judging baseline checks that are directly supported by approved annotations, such as missing image, no ink, unsupported target, or absent bundle.
4. Keep form comparison and stroke comparison in separate modules and test suites.

**Done when:** Both branches have stable contracts and independently report why validation cannot yet run.

### Step 5 — Implement hybrid decision policy

1. Write tests covering every pair of form/stroke branch states: unavailable, pass, fail, uncertain, and contradictory evidence.
2. Implement a versioned policy that only produces an overall pass/fail when both branches are available and their expert-approved thresholds are present.
3. Preserve every branch result in the hybrid response. Do not reduce a disagreement to one unexplained boolean.
4. Add tests proving a hybrid response cannot claim a pass before approved form and stroke criteria exist.

**Done when:** The combined result is auditable and cannot overstate current evidence.

### Step 6 — Add source retrieval and AI-feedback boundary

1. Write retrieval tests for target/rule/error-code mapping, missing sources, source-reference preservation, minimum-context selection, and prompt-injection-resistant treatment of source text as reference material rather than instructions.
2. Implement deterministic retrieval from the local knowledge graph before connecting any external model.
3. Write tests for the AI-feedback request schema and response validation. Include unsupported claims, invented errors, absent citations, service timeouts, and fallback feedback.
4. Add a provider adapter behind one interface. Do not hard-code API credentials or a provider-specific model into source control.
5. Log retrieval IDs, model/prompt version, latency, fallback use, and output-validation result without storing unnecessary learner data.

**Done when:** A validator result can produce traceable, constrained feedback or a safe deterministic fallback.

### Step 7 — Prepare Chapter 3 evaluation artifacts

1. Create a held-out evaluation-record schema that keeps expert label, form prediction, stroke prediction, hybrid prediction, retrieved sources, feedback rating, and timing separate.
2. Write metric tests for accuracy, precision, recall, F1-score, confusion matrices, and the error categories in Section 4.
3. Write separate RAG tests/data sheets for source correctness and feedback relevance, reviewed by qualified evaluators.
4. Ensure split logic is writer-level so samples from one writer do not appear in both training/tuning and held-out testing.
5. Document response-time measurement from validation request through final feedback display.

**Done when:** The team can collect Chapter 3/4 evidence without mixing expert template data, threshold-tuning data, and held-out evaluation data.

### Step 8 — Verify and document

1. Run backend and frontend test suites and a production build.
2. Check a synthetic `ba` flow from capture JSON through preprocessing, features, unavailable branch responses, hybrid response, retrieval, and deterministic feedback fallback.
3. Check malformed image data, missing source data, unsupported targets, a missing bundle, an AI timeout, and a response with invented error codes.
4. Update the developer README with asset locations, source provenance, expert workflow, privacy handling, current capability limits, and local run instructions.

**Done when:** The entire infrastructure is reproducible, source-traceable, and honestly reports that scoring awaits expert-approved data.

## 7. Acceptance criteria

- Each approved target can link image, stroke, source, and review evidence through one versioned reference bundle.
- Image and stroke processing are deterministic, independent, reproducible, and do not mutate original recordings.
- No branch or hybrid response returns a learner pass/fail before approved bundles and thresholds exist.
- The hybrid response retains both form and stroke findings and identifies its policy version.
- AI feedback is constrained to validator-provided errors and retrieved knowledge-graph sources, includes citations, and has a deterministic fallback.
- Chapter 3 evaluation data can separately measure form, stroke, hybrid, and RAG performance against expert-reviewed ground truth.
- Tests precede implementation; private recordings, reviewer details, generated artifacts, and credentials remain untracked.

## 8. Dependencies and sequencing

Work can begin immediately through the deterministic schemas, preprocessing, feature extraction, response contracts, retrieval, AI adapter interface, metric tooling, and synthetic tests.

The following require qualified expert reference work before they can become real validation behavior:

- approving character specifications, visual annotations, and canonical images;
- recording expert templates through the developer tool;
- selecting accepted visual/stroke variation and thresholds;
- training any machine-learning model;
- collecting expert-reviewed learner samples and reporting final performance metrics.

The recommended pilot remains `ba` and `ka`. Do not expand the initial scoring scope until their form and stroke templates, annotations, and expert review have been completed.