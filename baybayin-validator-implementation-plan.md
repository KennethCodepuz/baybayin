# Baybayin Validator Implementation Plan

> Historical roadmap. For delivered behavior and current limitations, use [app/docs/CURRENT_SYSTEM_STATUS.md](app/docs/CURRENT_SYSTEM_STATUS.md). This roadmap's original pending statements are not a live system-status report.

**Status:** Planning draft; character standards, expert involvement, and research constraints still need confirmation.  
**Purpose:** Build and evaluate a prototype that checks a selected Baybayin character's final form and writing process, and provides evidence-linked feedback.  
**Working constraint:** No application code until explicitly authorized.

## 1. Intended outcome and boundaries

The learner selects a supported target character, draws it on a canvas, and submits it. The system captures the final drawing and the writing sequence, evaluates the checks supported by the current version, and presents feedback linked to the relevant reference or expert-approved rule.

- **Version 1:** final-form conformance and capture of stroke data. A good final form does not establish that the writing process was correct.
- **Version 2:** form checks plus supported checks for stroke count, order, direction, trajectory, and kudlit placement. Report each applicable check separately as well as the overall result.
- **Explanation layer:** a source-traceable knowledge base and, where required and justified, a knowledge graph and retrieval-augmented generation (RAG). This layer explains checks; it does not decide whether a drawing passes.
- **Initial pilot:** propose three to five characters, including a consonant with an above-kudlit and a below-kudlit variation. Confirm the exact set after reviewing the source and thesis requirements. The final thesis scope remains to be decided.
- **Out of initial scope:** recognition of unrestricted words, general transliteration, and claims that the tool evaluates every legitimate Baybayin writing tradition.

## 2. Decisions needed before development

| Decision | Proposed approach | Evidence or confirmation needed |
|---|---|---|
| Authority and convention | Use identified KWF references for claims they actually support; document any additional expert-approved stroke convention separately. | Exact titles, editions, pages, permitted uses, and expert review. Do not assume the source prescribes stroke order or direction. |
| Character scope | Pilot a small, varied set; define the complete evaluation set before main collection. | Thesis objectives, available reference material, time, and expert capacity. |
| Expert review | Recruit qualified Baybayin reviewer(s); preferably two independently review a subset. | Qualifications, availability, disagreement procedure, and consent. |
| Capture environment | Choose supported devices and input methods after a capture pilot. | Availability of devices, input reliability, and study constraints. |
| Study population and sample size | Establish writer groups, repetitions, and error coverage after a pilot and a feasibility or sample-size justification. | Access to participants, expected variability, ethics requirements, and precision desired. |
| Graph and RAG | Confirm whether these are thesis requirements; implement the smallest justified retrieval approach. | Approved scope and a measurable purpose beyond a simple source lookup. |

## 3. Development workflow

### Phase 1 — Specify the reference and rubric

**Activities**

1. Gather the exact KWF materials and record title, edition, page or location, reference images, and provenance. Note rights or permissions needed for reuse.
2. For each pilot character and variant, document the target, reference form, accepted visual variations, applicable kudlit, and source-backed rules.
3. For each proposed stroke check, identify whether the reference supports it; otherwise mark it as a proposed study convention requiring expert approval. Record accepted alternatives and unresolved cases.
4. Draft a labeling rubric with observable criteria for overall form, stroke count, order, direction, trajectory, and kudlit placement. Permit multiple errors, unclear cases, and not-applicable labels.
5. Have the reviewer(s) assess sample drawings and trajectory replays. Revise the rubric and retain a versioned record of decisions.

**Deliverables:** source register; pilot character specifications; reviewer rubric; list of open questions and accepted conventions.  
**Exit criteria:** The pilot scope and rubric are approved for use by the research team and relevant reviewer(s); unsupported rules remain explicitly unresolved rather than being presented as KWF rules.

### Phase 2 — Design the capture and study protocol

**Activities**

1. Specify participant tasks, instructions, target selection, sample identifiers, and collection conditions. Plan both ordinary writing and clearly identified prompted errors; keep these categories distinguishable.
2. Define each captured record: pseudonymous writer and sample IDs, target character and variant, device/input type, canvas dimensions, final rendering, timestamps, ordered coordinates, and pen-down/pen-up events. Record capture and rubric versions.
3. Define incomplete or interrupted samples, quality checks, any exclusions, and how the reviewer accesses a stroke replay. Preserve the original event data when creating normalized copies.
4. Prepare consent, access controls, retention and deletion rules, and any required institutional ethics review before collecting participant data.
5. Run a small feasibility pilot after the capture tool exists; use it to refine instructions, device support, rubric, and collection targets. Do not silently mix pilot records collected under changing rules into the final evaluation.

**Deliverables:** data dictionary; task and consent materials; capture and quality-control protocol; pilot review checklist.  
**Exit criteria:** The protocol can distinguish writers and samples, preserve timing and stroke boundaries, and supply reviewers with sufficient evidence to label each intended check.

### Phase 3 — Build Version 1 and capture workflow

**Activities, once coding is authorized**

1. Build the target selector and drawing canvas with clear, reset, and submit actions, and store both final image and event sequence.
2. Implement image preprocessing that retains the relationship between the main character and its kudlit. Document coordinate and image transformations.
3. Establish a simple, reproducible form-comparison baseline using approved references. Determine thresholds on development data, then report form results independently of stroke results.
4. Test capture behavior for a dot or short mark, accidental pen lifts, incomplete drawings, different canvas sizes, and each supported input device. Verify that the event replay reproduces what was drawn.
5. Add a clear status for insufficient or unreliable input; avoid presenting unsupported stroke conclusions in Version 1.

**Deliverables:** Version 1 prototype; capture/replay workflow; documented form baseline and test results.  
**Exit criteria:** Pilot samples can be captured, replayed, stored, and reviewed; form decisions are reproducible; capture limitations are documented.

### Phase 4 — Collect and label the dataset

**Activities**

1. Finalize the sample plan before main collection: participant criteria, number of writers, repetitions per target, natural and prompted error categories, and minimum per-category reporting counts.
2. Collect and quality-check records using the approved protocol. Maintain pseudonymous identifiers and keep consent records separate from research samples.
3. Have qualified reviewers label final form and temporal stroke checks from the appropriate evidence. Independent duplicate review of a subset, where feasible, supports agreement reporting; resolve disagreements using a documented process.
4. Mark prompted-error instructions separately from the expert's observed labels. A requested error does not prove that the participant actually produced it.
5. Freeze the dataset version and assign writers—not individual drawings—to development, validation, and held-out test groups. Record any exclusions and prevent participant overlap.

**Deliverables:** versioned dataset and data dictionary; reviewed labels; reviewer agreement and adjudication record; split manifest.  
**Exit criteria:** Each evaluated category has documented expert labels and sample counts; test writers remain untouched for tuning; data handling follows the approved protocol.

### Phase 5 — Develop Version 2 stroke validation

**Activities**

1. Segment recorded strokes using pen events; normalize and resample trajectories while preserving order, direction, and relative placement. Document preprocessing choices and input-quality checks.
2. Compare candidate methods against a simple baseline. Evaluate count and rule checks, sequence matching, trajectory similarity, and kudlit position only where an approved rubric and sufficient labeled data exist.
3. Use development data to build methods and validation writers to select thresholds and configuration. Support approved alternative writing patterns where documented.
4. Define how individual check results combine into an overall decision. Allow unclear or insufficient-data outcomes rather than forcing a binary judgment when evidence is inadequate.
5. Verify that the feedback names the actual failed check and does not claim to detect an error that was not evaluated.

**Deliverables:** Version 2 prototype; documented features, checks, thresholds, and decision rules; development and validation results.  
**Exit criteria:** Each claimed check can be reproduced and mapped to a rubric criterion, with measured validation performance and documented limitations.

### Phase 6 — Build the evidence and explanation layer

**Activities**

1. Store character records, approved rules, source references, and associated explanations with stable identifiers and version information.
2. Map each validator outcome to an approved rule and reference. Begin with deterministic source lookup as a baseline; add graph relationships and RAG if the research scope requires them or their contribution is justified.
3. If generated explanations are used, restrict them to retrieved evidence and the actual validator result; provide a safe fallback when the evidence is unavailable or inconsistent.
4. Separately review retrieval source correctness and feedback relevance, including missing-source and wrong-rule cases. Track whether explanations accurately describe the detected error.

**Deliverables:** traceable knowledge base; feedback mapping; retrieval and explanation evaluation protocol and results.  
**Exit criteria:** Feedback identifies the relevant source and reflects the measured result; unsupported or missing evidence is handled explicitly.

### Phase 7 — Final evaluation and thesis reporting

**Activities**

1. Freeze the system, selected thresholds, rubric, and analysis plan before evaluating held-out writers. Run the final evaluation once under the documented protocol.
2. Evaluate form-only, stroke-only, and combined decisions as applicable. Compare with expert-reviewed ground truth, including error-specific outcomes and results for naturally occurring versus prompted errors.
3. Define the positive class for every metric. Report confusion matrices, precision, recall, F1, accuracy where meaningful, sample and writer counts, and uncertainty where the data support it. Report sparse categories without overstating conclusions.
4. Analyze failures by character, error, writer, and device where sample sizes permit. Report reviewer agreement and unresolved or excluded cases. Measure response time if it is a stated goal.
5. Evaluate retrieval and explanations separately from validation accuracy. Document reproducibility, limitations, and the scope of the supported writing convention in Chapters 3 and 4.

**Deliverables:** frozen evaluation report, error analysis, reproducibility record, and thesis-ready methodology and results.  
**Exit criteria:** The research questions can be answered with transparent evidence and limitations; no test data were used to set the reported model or thresholds.

## 4. High-level component flow

1. **Input:** selected target and captured drawing events.
2. **Capture and storage:** original strokes, final image, and pseudonymous metadata.
3. **Preprocessing:** input quality, coordinate normalization, stroke segmentation, and spatial relationships.
4. **Validation:** form check plus applicable stroke and kudlit checks; combine results using documented rules.
5. **Evidence retrieval:** map results to approved rules and their sources.
6. **Output:** per-check feedback, overall or inconclusive result, and relevant evidence.

The knowledge base supplies documented rules and references; it does not independently override the validator's decision. Actual technologies and hosting should be chosen after scope, devices, data-handling requirements, and available resources are known.

## 5. Immediate work queue

1. Obtain the exact KWF documents and confirm whether the knowledge graph and RAG are mandatory thesis components.
2. Select the pilot characters and variants with the research team.
3. Create one source-linked character specification and a draft rubric; mark all unsupported stroke claims for expert review.
4. Identify reviewer(s) and test the rubric against a few example drawings and their stroke replays, or arrange reference demonstrations if replays do not yet exist.
5. Draft the capture data dictionary and participant protocol. Once these are reviewed and coding is authorized, begin Version 1.

## 6. Key risks and responses

| Risk | Response |
|---|---|
| Reference material does not prescribe a stroke sequence. | Treat sequence as an explicitly selected, expert-reviewed study convention; avoid attributing it to KWF without evidence. |
| A correct-looking form uses an unaccepted or unobserved sequence. | Evaluate final form and process separately; do not infer a stroke sequence from a static image. |
| Prompted errors differ from real learner mistakes. | Include ordinary writing and report prompted and natural cases separately. |
| Too few examples for some error types. | Pilot recruitment and labeling first; disclose counts and avoid broad claims for sparse categories. |
| Capture artifacts resemble writing errors. | Test supported devices, retain raw events, define quality checks, and allow an inconclusive result. |
| Retrieval or generated feedback misrepresents the result. | Map feedback to actual check outcomes and inspect source correctness and explanation accuracy separately. |

## 7. Source and assumptions

This plan extends the supplied *Hybrid Baybayin Character and Stroke Validation System* development plan. It does not establish the content of KWF materials or imply that an expert, participant sample, ethics approval, or data already exists. All such items are pending confirmation.
