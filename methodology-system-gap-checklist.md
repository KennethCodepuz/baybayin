# Chapter 3 Methodology: System Gap Checklist

**Source reviewed:** `tmp/pdfs/methodology/Chapter3_Methodology.pdf`  
**Text used for cross-checking:** `chapter3_extracted.txt`  
**Review date:** 2026-10-23

## Status definitions

- [ ] **Missing** — no implementation or evidence was found.
- [~] **Partial** — some supporting infrastructure exists, but it does not satisfy the methodology.
- [x] **Implemented** — the current repository provides the required behavior. This does not mean it has been experimentally validated.

The current application is a capture, replay, reference-curation, and structural-validation prototype. It must not be presented as satisfying the methodology's validator or evaluation requirements until the items below are completed.

## 3.1 Research design and research process

### Research design

- [ ] Implement and document the R&D workflow as a research protocol, not only as an application build.
- [ ] Implement the experimental performance evaluation under identical data, writer-level splits, fixed metrics, and fixed evaluation conditions.
- [~] Keep the two connected versions separate:
  - [x] The capture stores a final image and ordered pointer events.
  - [ ] Version 1 must perform final-form validation using only the final image.
  - [ ] Version 2 must validate count, order, direction, trajectory/shape, and kudlit placement.
  - [ ] Report Version 1 and Version 2 independently as well as together.
- [~] Keep the knowledge graph and retrieval layer explanatory only:
  - [x] The current feedback boundary is designed not to change validation outcomes.
  - [ ] The actual measurable validators must exist before the retrieval layer can explain their results.
- [ ] Implement the four research phases end to end:
  - [ ] Data collection producing character specifications, knowledge-base records, and labeled data.
  - [ ] Preprocessing cleaning, normalization, segmentation, and resampling.
  - [ ] Model implementation for Version 1, Version 2, and evidence retrieval.
  - [ ] Performance evaluation on writers held out from development.
- [ ] Produce reproducible inputs and outputs for each phase, with versioned artifacts and run metadata.

## 3.2 Locale of the study

- [ ] Confirm and document Mariano Marcos State University, College of Computing and Information Sciences, City of Batac, Ilocos Norte as the study locale.
- [ ] Conduct system development and writing sessions at the specified locale, or document and obtain approval for any change.
- [ ] Use the same type of touchscreen device for writing sessions.
- [ ] Record the device model, operating system, browser, and input hardware for every session.

## 3.3 Participants and data sources

### Volunteer writers

- [ ] Recruit adults aged 18 or older.
- [ ] Support writers with no, basic, and experienced Baybayin knowledge.
- [ ] Record each writer's experience level as study metadata.
- [ ] Recruit the target of 20 writers, or document an approved change and its justification.
- [ ] Record informed consent before any writing session.
- [ ] Ensure writers can write on the supported touchscreen device.

### Expert reviewer

- [ ] Recruit and document the qualifications of a Baybayin orthography expert.
- [ ] Have the expert approve the character specification and rubric.
- [ ] Have the expert confirm reference strokes.
- [ ] Have the expert label every sample.
- [ ] Use a second reviewer for the planned subset if available and record disagreement/adjudication procedures.

### KWF and documentary sources

- [ ] Obtain and document the exact *Pinagyamang Baybayin* Version 3 source.
- [ ] Obtain and document the expert's writing guide.
- [ ] Obtain the symbol files containing correct strokes.
- [ ] Record source edition, page, provenance, permission, and citation metadata.
- [~] The repository has source-linked graph records and PDF page references, but the current source register and reference documentation still contain pending verification items.

## 3.4 Research instruments

### Drawing canvas

- [~] A web drawing canvas exists.
- [ ] Match the methodology's fixed 400 × 400 pixel canvas.
- [ ] Match the fixed 8 pixel pen width.
- [x] Save the final image.
- [x] Save ordered stroke records with x, y, time, pen-down, and pen-up events.
- [ ] Provide a reference-tracing mode showing the numbered reference strokes and direction arrows.
- [ ] Ensure the same canvas and pen settings are used for reference traces and participant samples.

### Task sheet

- [ ] Create a randomized target-character task sheet.
- [ ] Include the instruction for each attempt: write correctly or produce a specified controlled error.
- [ ] Persist the exact instruction given with each sample.
- [ ] Record the random seed used to generate each writer's character order.

### Expert checklist

- [ ] Create a labeling interface/form with five yes/no checks:
  - [ ] Form.
  - [ ] Stroke count.
  - [ ] Stroke order.
  - [ ] Stroke direction.
  - [ ] Kudlit placement.
- [ ] Include an overall valid/invalid label.
- [ ] Include reviewer remarks.
- [ ] Support unclear/not-applicable or equivalent adjudication states where required by the approved rubric.

### Knowledge graph

- [~] A read-only source-traceable knowledge graph exists.
- [ ] Add the methodology's complete node model:
  - [ ] Character: ID, name, KWF category.
  - [ ] Stroke: order number, direction description, reference trajectory.
  - [ ] KudlitRule: type, resulting sound, expected relative position.
  - [ ] ReferenceImage: file path and description.
  - [ ] ErrorType: name, description, feedback template.
  - [ ] Source: document, edition, page.
- [ ] Link every node to at least one source node.
- [ ] Add reference stroke trajectories and approved character-specific rules, not only catalog/source metadata.
- [ ] Add common errors and feedback templates for the five methodology error categories.

### Evaluation scripts

- [ ] Implement scripts for accuracy, precision, recall, F1, confusion matrices, error-specific results, response time, and statistical testing.
- [ ] Make scripts consume a frozen test-set manifest and versioned validator outputs.

### Consent form

- [ ] Create the participant information sheet and written consent form.
- [ ] Record consent status and consent version without putting names in sample records.
- [ ] Obtain ethics clearance before participant collection.

### Sample record

- [~] Current JSON includes version, creation time, target, canvas, image, and events.
- [ ] Add sample ID.
- [ ] Add pseudonymous writer code.
- [ ] Add experience level.
- [ ] Add device and input type.
- [ ] Add character ID distinct from a display label where applicable.
- [ ] Add attempt number.
- [ ] Add the instruction given.
- [ ] Add session ID.
- [ ] Add labeler and label date after review.
- [ ] Add preprocessing/specification/rubric versions.
- [ ] Preserve the final image path or immutable image reference in the research dataset.
- [x] Preserve ordered points with x, y, timestamp, pen-down, and pen-up semantics.
- [ ] Define and implement the methodology's exact 400×400 coordinate convention.

## 3.5 Data-gathering procedure

### 3.5.1 Character specification and expert rubric

- [ ] With the expert, choose and freeze the initial character set.
- [ ] Include the titik-batayan characters and selected consonant kudlit forms as applicable.
- [ ] Place the final character list in Appendix A or the approved equivalent.
- [ ] For every character, record:
  - [ ] Character ID and name.
  - [ ] KWF category.
  - [ ] Number of strokes.
  - [ ] Order of each stroke.
  - [ ] Direction of each stroke.
  - [ ] Which stroke is the kudlit, if any.
  - [ ] Source page.
- [ ] Implement researcher tracing of every reference stroke on the same drawing canvas.
- [ ] Have the expert check and approve every reference trace.
- [ ] Store multiple approved references when the guide accepts more than one writing form.
- [ ] Mark characters with nearly identical stroke shapes.
- [ ] Disable order scoring for characters explicitly marked as order-indistinguishable.
- [ ] Approve and version the rubric before participant labeling.
- [ ] Implement the five methodology error categories and their controlled-error instructions:
  - [ ] Form: intentionally change one stroke shape.
  - [ ] Count: omit or add a stroke.
  - [ ] Order: draw strokes in another sequence.
  - [ ] Direction: draw one stroke from the opposite end.
  - [ ] Kudlit placement: put the kudlit on the opposite side.
- [ ] Document which errors Version 1 can detect, partly detect, or cannot detect.

### 3.5.2 Knowledge-base construction

- [~] The repository has JSON graph files and source-linked targets.
- [ ] Populate the complete methodology node/edge structure listed in Table 12.
- [ ] Add expert-approved reference images and reference stroke trajectories.
- [ ] Add exact rule records for count, order, direction, form, and kudlit placement.
- [ ] Add error descriptions and feedback templates.
- [ ] Ensure every explanation can retrieve the character, applicable rule, error type, and source.
- [ ] Provide a queryable graph/database representation if the final thesis requires the stated node and edge tables; the current implementation reads committed JSON rather than a project database.
- [ ] Version graph changes and retain dated change records.

### 3.5.3 Writing task and sample collection

- [ ] Implement consent and experience-level collection before writing.
- [ ] Provide blank-canvas practice before scored attempts.
- [ ] For every target, display the reference image with numbered strokes and arrows for order/direction.
- [ ] Collect four attempts per character:
  - [ ] Two instructed correct attempts.
  - [ ] Two instructed controlled-error attempts.
- [ ] Rotate the two controlled-error categories equally for each character.
- [ ] Implement the specified assignment:
  `Ac[(w + c) mod |Ac|]` and `Ac[(w + c + 1) mod |Ac|]`, with writer and character indexes starting at zero.
- [ ] Randomize character order separately for each writer.
- [ ] Use and persist a fixed random seed.
- [ ] Save one complete record per attempt.
- [ ] Detect accidental marks and technical problems.
- [ ] Repeat unusable attempts.
- [ ] Log every discarded attempt and its reason.
- [ ] Generate the expected sample count `W × C × 4` and reconcile it with the actual collection manifest.
- [ ] For the example design, support 20 writers × 24 characters × 4 = 1,920 base samples before extra kudlit forms.

### 3.5.4 Expert labeling

- [ ] Build a labeling page showing the final image and stroke replay.
- [ ] Show stroke numbers, start dots, and direction arrows.
- [ ] Hide writer code and the instruction given to prevent labeler bias.
- [ ] Store five yes/no labels and the overall valid/invalid label.
- [ ] Treat the expert label as ground truth in evaluation.
- [ ] Report agreement between the assigned instruction and expert label.
- [ ] Report intended-correct samples labeled invalid as natural errors.
- [ ] Randomly select 10% of samples for repeat labeling by the same expert.
- [ ] Enforce at least a 7-day interval before repeat labeling.
- [ ] Calculate and report repeat-label percent agreement.
- [ ] Produce an expert-reviewed stroke-level dataset with immutable label/version metadata.

## 3.6 Data cleaning and preprocessing

### 3.6.1 Removing incomplete records

- [~] The API rejects missing/invalid fields, empty event lists, non-increasing timestamps, and incomplete stroke sequences.
- [ ] Apply cleaning to the research dataset, not only at request validation time.
- [ ] Remove records with missing fields.
- [ ] Remove records with no strokes.
- [ ] Remove records whose point times do not increase.
- [ ] Keep very short strokes because a kudlit can be a dot.
- [ ] Let the expert mark accidental marks.
- [ ] Repeat and log attempts marked unusable.
- [ ] Preserve the original raw record while storing a cleaned derivative and exclusion reason.

### 3.6.2 Image normalization for Version 1

- [~] Current code crops visible ink and preserves aspect ratio, but produces a 256×256 grayscale image.
- [ ] Crop to the ink bounding box.
- [ ] Scale the longest side to exactly 56 pixels.
- [ ] Center the result in a 64×64 image.
- [ ] Convert to a binary image with ink = 1 and background = 0.
- [ ] Draw reference images with the same pen width.
- [ ] Process reference and participant images through the identical normalization pipeline.
- [ ] Preserve the original image and record normalization parameters/version.

### 3.6.3 Stroke segmentation, normalization, and resampling for Version 2

- [~] Current code segments down/move/up events and normalizes points by canvas dimensions, but does not implement the required pipeline.
- [ ] Define a stroke as pen-down through the next pen-up.
- [ ] Smooth every stroke with a 3-point moving average while keeping the first and last points.
- [ ] Move and scale the whole character into a unit box while preserving aspect ratio.
- [ ] Preserve the kudlit's position relative to the main body.
- [ ] Resample every stroke to exactly 32 points at equal arc-length intervals.
- [ ] Apply the same preprocessing to reference strokes.
- [ ] Implement and test Algorithm 1.
- [ ] Verify Algorithm 1 is O(n) in the total number of raw points.
- [ ] Store derived strokes without overwriting raw events.
- [ ] Add tests for dots, one-point/zero-length paths, multiple strokes, and scale/translation invariance.

## 3.7 Feature extraction

- [ ] Implement Version 1 form similarity as binary-image Dice similarity:
  `Dice(A,B) = 2|A∩B| / (|A|+|B|)`.
- [ ] Dilate both binary images by one pixel using a 3×3 block before Dice comparison.
- [ ] Implement Version 2 stroke-count difference.
- [ ] Implement order matching based on shape pairing.
- [ ] Implement reversed-stroke comparison for direction.
- [ ] Implement per-paired-stroke shape distance:
  `d(s,r) = (1/N) × Σ ||p_i − q_i||`, with `N = 32`.
- [ ] Implement kudlit offset using relative kudlit/main-body coordinates.
- [ ] Implement zero-width/zero-height protection by replacing zero dimensions with 1.
- [ ] Return reproducible feature records with sample ID, target, reference ID, and feature schema version.
- [ ] Add tests with known positive and negative feature values.
- [ ] Do not treat the current endpoint's structural acceptance or current feature extraction as a correctness result.

## 3.8 Model implementation

### 3.8.1 Data split and threshold setting

- [ ] Split writers, never individual samples, into development and test sets.
- [ ] Use the methodology's 80/20 split: 16 development writers and 4 test writers for 20 writers.
- [ ] Select writers randomly with a fixed recorded seed.
- [ ] Ensure no writer appears in both sets.
- [ ] Use four-fold cross-validation by writer inside development, with four writers per fold.
- [ ] Search 50 equally spaced candidate values between the development minimum and maximum for each threshold.
- [ ] Select the candidate with the highest mean validation F1.
- [ ] Select the smaller threshold on ties.
- [ ] Tune `τform` using all invalid samples as positive and valid samples as negative.
- [ ] Tune `τshape` and `τkudlit` using the corresponding expert error labels.
- [ ] Freeze thresholds before accessing the test set.
- [ ] Record threshold values, candidate grid, folds, seed, dataset version, and software version.
- [ ] Keep count, order, and direction exact, with no learned threshold.

### 3.8.2 Version 1 form validator

- [ ] Retrieve the target's approved reference image.
- [ ] Normalize learner and reference images to 64×64 binary images.
- [ ] Dilate both by one pixel.
- [ ] Compute Dice similarity.
- [ ] Return form-valid when similarity is at least `τform`; otherwise form-invalid.
- [ ] Ensure Version 1 receives no stroke-event information.
- [ ] Report Version 1 complexity as O(P) for P image pixels.

### 3.8.3 Version 2 stroke validator

- [ ] Retrieve normalized target reference strokes, `τshape`, `τkudlit`, and optional kudlit index.
- [ ] Implement Algorithm 2 exactly:
  - [ ] If drawn count differs from reference count, report count and skip other checks.
  - [ ] Compute `D[i][j] = min(d(s_i,r_j), d(rev(s_i),r_j))`.
  - [ ] Try all possible pairings and retain the minimum-total-distance pairing.
  - [ ] Report order when the pairing is not the same-sequence pairing.
  - [ ] Report direction when the reversed distance is smaller.
  - [ ] Report stroke form when paired distance exceeds `τshape`.
  - [ ] Report kudlit when relative-position offset exceeds `τkudlit`.
  - [ ] Skip order for characters marked order-indistinguishable.
- [ ] Return an empty error list only when every applicable check passes.
- [ ] Verify the stated complexity `O(n + K²N + K·K!)`.
- [ ] Add deterministic tests for count, order, direction, shape, and kudlit errors.

### 3.8.4 Hybrid decision and evidence retrieval

- [~] The current API has a hybrid response contract and deterministic feedback boundary, but scoring remains unavailable.
- [ ] Run preprocessing for both image and raw strokes.
- [ ] Retrieve the approved reference tuple `(R, refImage, κ)` by target.
- [ ] Run Version 1 and Version 2.
- [ ] Return valid only when Version 1 passes and Version 2 reports no applicable errors.
- [ ] Return invalid with all detected errors otherwise.
- [ ] Retrieve, for each error, the character record, matching stroke/kudlit rule, error template, and linked source.
- [ ] Fill a deterministic source-grounded explanation.
- [ ] If a language model is used, restrict it to rewording retrieved text and prohibit changing the result or adding errors.
- [ ] Include the reference image and its source in the user-facing result.
- [ ] Verify the stated hybrid complexity `O(n + P + K²N + K·K! + |E|·q)`.

### 3.8.5 Fixed parameters

- [ ] Set canvas to 400×400 pixels and pen width to 8 pixels.
- [ ] Set target writer count to 20.
- [ ] Set attempts to four per character: two correct and two controlled-error.
- [ ] Set smoothing window to three points.
- [ ] Set 32 points per stroke.
- [ ] Set normalized image to 64×64 with longest side 56 pixels.
- [ ] Set one-pixel dilation.
- [ ] Set writer split to 80% development and 20% test.
- [ ] Set four writer-level cross-validation folds inside development.
- [ ] Set threshold search to 50 equally spaced values with highest mean validation F1.
- [ ] Learn and freeze `τform`, `τshape`, and `τkudlit` from development data.
- [ ] Fix and record all random seeds.
- [ ] Add configuration validation so production runs cannot silently use different parameters.

## 3.9 Performance evaluation

### 3.9.1 Ground truth and evaluation design

- [ ] Compare every decision with the expert-reviewed label.
- [ ] Treat invalid/form-error as the positive class.
- [ ] Evaluate Version 1 alone, Version 2 alone, and the complete hybrid on the same test samples.
- [ ] Report controlled-error and natural-error results separately.
- [ ] Use the test set once, after thresholds are frozen.

### 3.9.2 Metrics

- [ ] Compute TP, TN, FP, and FN using the methodology's definitions.
- [ ] Compute accuracy.
- [ ] Compute precision.
- [ ] Compute recall.
- [ ] Compute F1-score.
- [ ] Report a confusion matrix for each validator.
- [ ] Define zero-denominator behavior explicitly and report it rather than silently substituting a value.

### 3.9.3 Error-specific results

- [ ] For form, count, order, direction, and kudlit, compute detection recall.
- [ ] Compute identification accuracy for each error category.
- [ ] Report where Version 2 detects errors that Version 1 cannot show.
- [ ] Preserve multi-label errors when a sample has more than one error.

### 3.9.4 Evidence retrieval evaluation

- [ ] Randomly select 100 invalid test outputs, or all invalid outputs if fewer than 100.
- [ ] Give the selected outputs to the expert.
- [ ] Collect source correctness (yes/no).
- [ ] Collect feedback relevance/clarity rating from 1 to 5.
- [ ] Report share of correct sources.
- [ ] Report mean rating.
- [ ] Report share of ratings equal to 4 or 5.

### 3.9.5 Response time

- [ ] Measure from drawing submission until the result and explanation return.
- [ ] Measure in the backend for every test sample.
- [ ] Run on the same computer.
- [ ] Record computer specifications.
- [ ] Report mean and maximum response time.
- [ ] Store timing with the validator run version and sample ID.

### 3.9.6 Statistical treatment

- [ ] Summarize results as counts and percentages.
- [ ] Compare Version 1 and Version 2 on the same test samples.
- [ ] Compare whether each decision matches the expert label.
- [ ] Implement McNemar's test at alpha = 0.05.
- [ ] Report the number of samples behind every result because the test set has few writers.
- [ ] Record the statistical software/version and exact test configuration.

## 3.10 System development method and model utilization

- [~] A React/Next.js frontend and FastAPI backend exist.
- [ ] Integrate preprocessing, Version 1, Version 2, and retrieval into the backend request path.
- [ ] Let the user select a target, draw, and receive a real validation result.
- [ ] Show the result, explanation, reference image, and source.
- [ ] Keep the system a validation tool, not a learning platform.
- [ ] Implement Version 1's form-conformance claim.
- [ ] Implement Version 2's stroke-validation claim.
- [ ] Document and execute Agile iterations with inputs, activities, outputs, and objective mapping:
  - [ ] Iteration 1: source/rubric and character specifications.
  - [ ] Iteration 2: capture and data collection.
  - [ ] Iteration 3: Version 1 image validator.
  - [ ] Iteration 4: Version 2 stroke validator.
  - [ ] Iteration 5: evaluation and integration.
- [ ] Preserve iteration decisions and changes to collection/rubric/model assumptions.
- [ ] Produce the final prototype and Chapter 4 result artifacts.

## 3.11 Ethical considerations and data management

- [ ] Obtain MMSU ethics clearance before participant collection.
- [ ] Follow the Philippine Data Privacy Act of 2012 (Republic Act No. 10173).
- [ ] Provide an information sheet explaining purpose, recorded data, voluntary participation, and withdrawal.
- [ ] Obtain signed consent before writing.
- [ ] Store samples under pseudonymous writer codes.
- [ ] Keep names and the code key only in consent records separate from research samples.
- [ ] Restrict data to a password-protected location accessible only to researchers and the expert.
- [ ] Use KWF and expert reference materials with permission.
- [ ] Cite sources and do not share restricted materials outside the authorized group.
- [ ] Keep writer code, session, device, character, attempt number, labeler, and label date in every sample record.
- [ ] Record character-specification version for every evaluation run.
- [ ] Record threshold values for every evaluation run.
- [ ] Record random seeds for every evaluation run.
- [ ] Record software version for every evaluation run.
- [ ] Link every knowledge-graph record to its source.
- [ ] Log graph and data changes with dates.
- [ ] Define retention, deletion, withdrawal, backup, and breach-response procedures.
- [ ] State that the validator assists checking and does not replace Baybayin expert judgment.

## Highest-priority implementation blockers

These items prevent the system from making the methodology's intended validation claim:

- [ ] Obtain expert-approved character specifications, reference strokes, accepted variants, and rubric.
- [ ] Implement the exact preprocessing pipeline: 64×64 binary image normalization, 3-point smoothing, unit-box normalization, and 32-point arc-length resampling.
- [ ] Implement Version 1 Dice comparison with one-pixel dilation.
- [ ] Implement Version 2 count, pairing/order, direction, shape-distance, and kudlit-offset checks.
- [ ] Collect and label the writer-level dataset using the four-attempt controlled-error protocol.
- [ ] Implement writer-level development/test splitting, four-fold cross-validation, and threshold selection.
- [ ] Implement the complete evaluation and statistical reporting pipeline.
- [ ] Implement blinded expert labeling and repeat-label agreement.
- [ ] Add the required consent, anonymization, access control, traceability, and ethics workflow.
- [ ] Update the UI/API so unavailable scoring is replaced only after the above evidence and validation controls are complete.

