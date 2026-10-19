# Draft pilot character specifications: ba and ka

**Status:** Draft for expert review, 19 October 2026. These are not approved validation rules or ground-truth labels.  
**Purpose:** Translate the supplied illustrations into questions and candidate checks for a small pilot. The validator should only enforce criteria after the research team and a qualified reviewer have agreed on them.

## Source and scope

- Source: Joel Bagain Lopez, *Pagsulat ng Baybayin* ([supplied PDF](../../Pagsulat-ng-Baybayin_Step-by-Step.pdf)). Its title page also displays the cover of *Pinagyamang Baybayin: Gabay sa Episyente, Modernisado, at Estandardisadong Pagsulat*.
- Page references below are PDF page numbers, counting the title page as page 1.
- The PDF distinguishes “Sinaunang Baybayin” and “Pinagyamang Baybayin” on pages 2–3. The handwriting diagrams appear under the Pinagyamang Baybayin material. The team must confirm that this convention is the intended study scope and verify how it relates to the KWF standard in the original plan.
- This draft covers the unmodified targets labeled **ba** and **ka** on their respective pages. It does not yet define kudlit variants; the source shows kudlit examples separately on PDF pages 36–37.
- The source gives numbered diagrams, but no clear legend in the PDF establishes whether every number is a separate pen stroke, a point along a path, or another kind of instruction. Do not derive a pen-lift count or precise sequence from the numbers without expert confirmation.

## Character 1: ba

| Field | Draft specification |
|---|---|
| Target label | `ba` |
| Reference | PDF page 7 |
| Direct observation | The page presents the completed form beside a grid-based diagram of the same form, with red numbers 1–4 placed around its path. |
| Form description for orientation | The illustrated form has two rounded sides meeting at a top peak and a central inward notch at the bottom. The PDF image remains the reference; this description is not a numerical acceptance rule. |
| Meaning of numbered marks | **Pending expert interpretation.** The marks appear around a continuous-looking path; they must not be counted as four pen strokes without confirmation. |
| Number of pen-down-to-pen-up strokes | Pending expert decision. |
| Stroke order, direction and paths | Pending expert decision, including start/end points and any pen lifts. |
| Accepted visual and writing variations | Pending expert decision. |
| Kudlit | Not included in this initial `ba` target; variants to be specified separately. |
| Reviewer and approval date | Pending. |

### Questions for the reviewer

1. What do the numbers 1–4 on page 7 indicate? In what order should the illustrated path be followed?
2. Where should the pen start and finish? Is the form intended to be made without lifting the pen? Are other sequences or pen-lift patterns acceptable?
3. Which changes in width, height, curvature, slant, or closure still count as this form under the selected convention?
4. What visible difference would make the form incorrect, and what cases should be marked unclear?

## Character 2: ka

| Field | Draft specification |
|---|---|
| Target label | `ka` |
| Reference | PDF page 15 |
| Direct observation | The page presents the completed form beside a grid-based diagram with red numbers 1–4 near portions of the form. |
| Form description for orientation | The illustration has upper and lower curved sections connected by a central vertical section. The PDF image remains the reference; this description is not a numerical acceptance rule. |
| Meaning of numbered marks | **Pending expert interpretation.** Their presence alone does not establish four pen-down-to-pen-up strokes. |
| Number of pen-down-to-pen-up strokes | Pending expert decision. |
| Stroke order, direction and paths | Pending expert decision, including start/end points, joins, and any pen lifts. |
| Accepted visual and writing variations | Pending expert decision. |
| Kudlit | Not included in this initial `ka` target; variants to be specified separately. |
| Reviewer and approval date | Pending. |

### Questions for the reviewer

1. What do the numbers 1–4 on page 15 indicate? What is the intended progression through the upper, lower, and connecting sections?
2. Where does each pen-down-to-pen-up stroke start and finish? Which pen lifts and alternative sequences are acceptable?
3. How should joins, curvature, proportions, and orientation be judged, including hand-drawn variation?
4. What visible difference would make the form incorrect, and what cases should be marked unclear?

## Shared draft review checklist

Use the selected character's reviewed specification together with the final image and a replay of its recorded events. The current app can replay the drawing in the current session and download JSON; importing a saved JSON for later replay is not implemented yet.

| Check | Evidence to inspect | Decision |
|---|---|---|
| Capture quality | Recording contains the full intended drawing; interruptions or accidental pen lifts are documented. | Pass / fail / unclear |
| Final form | Final image compared with the source and approved variations. | Pass / fail / unclear |
| Stroke count | Number of recorded pen-down-to-pen-up traces compared with the approved count or alternatives. | Pass / fail / unclear / not established |
| Stroke order | Replay and event sequence compared with approved alternatives. | Pass / fail / unclear / not established |
| Stroke direction | Replay and event direction compared with approved instructions. | Pass / fail / unclear / not established |
| Trajectory and joins | Recorded paths and their spatial relationships compared with approved variations. | Pass / fail / unclear / not established |
| Kudlit | Not part of these initial unmodified targets. | Not applicable |

The categories above are proposed review fields, not complete pass/fail definitions. An expert must define observable criteria and examples before they are used to label a study dataset. Multiple errors can occur in one drawing; an unclear capture should not be forced into pass or fail. Numerical tolerances and similarity thresholds remain unset until supported by expert review and development/validation data.

## Candidate reference-recording procedure

1. Ask the qualified reviewer to inspect the relevant page and explain the marks, start and end points, pen lifts, and any allowed variants. Record the interpretation and its provenance.
2. For each approved formation, have the reviewer draw a few examples in the app. Enter `ba` or `ka` as the target label and download each JSON separately. Record device and input method in a separate pilot log; do not enter a participant's name in the target field.
3. Review the final form and replay in the drawing session, and retain the downloaded event data. Do not assume an example is correct solely because it was intended as a reference; have it reviewed against the agreed specification.
4. Identify ambiguities and update this draft with the reviewer's decision, date, and specification version. If reviewers disagree, record how the decision is resolved.
5. After the study protocol and any required ethics review are in place, collect and label separate learner examples. Keep held-out writers separate from reference development and threshold tuning when evaluating performance.

**Video:** Optional supporting material for clarifying or demonstrating the drawing. It does not replace the expert-reviewed event recordings or rubric.
