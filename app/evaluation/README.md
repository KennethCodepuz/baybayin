# Evaluation dataset preparation

This directory contains only schemas and synthetic examples. Do not commit real expert recordings, participant identifiers, consent forms, reviewer names, or unapproved results.

The running application has local prototype scores only for `a`, `ba`, `e`, `i`, `o`, and `u`. Those practice limits are not an evaluation dataset and must not be used to report thesis metrics. `be`, `bi`, `bo`, `bu`, `b`, and `b_` currently have expert comparisons but no scoring thresholds. See [the current system status](../docs/CURRENT_SYSTEM_STATUS.md).

Use one evaluation record per held-out drawing after an expert has supplied the ground-truth decision. Keep these data partitions separate:

- **reference:** approved expert examples used to build bundles;
- **calibration:** separately labeled samples used to select thresholds;
- **held-out evaluation:** writer-disjoint, expert-labeled samples used only for final measures.

The backend module `evaluation_metrics.py` can calculate binary accuracy, precision, recall, F1-score, and a confusion matrix for each error code. Report form, stroke, hybrid, and error-specific metrics separately. Source-correctness and feedback-relevance ratings are separate fields because they evaluate retrieval/feedback rather than character recognition.

Use anonymous writer and reviewer codes. Store the mapping to real identities under the team’s approved private research storage, outside this repository.
