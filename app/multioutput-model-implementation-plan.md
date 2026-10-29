# Multi-output model validation plan

**Status:** Implemented as a preliminary local prototype on 2026-10-28.

## Scope

The model compares a learner recording with its matching expert reference recording and returns separate preliminary outputs for form, stroke count, stroke process, and applicable kudlit/cancellation-mark placement.

## Labels and limits

Group-protocol labels map `wrong_form`, `wrong_count`, `wrong_process`, and `wrong_kudlit` to four binary output models. `intended_conforming` is negative for each output. Kudlit is unavailable for `a`, `e`, `i`, `o`, `u`, and `ba`.

Generic `wrong_process` remains a process label. It is not used to claim separate direction or order classification.

## Implementation

1. Extract the fixed `pilot-v1` expert-reference-relative image and stroke features.
2. Evaluate one weighted forest per validation output with leave-one-writer-out folds.
3. Train a separate deployment model on all current rows only after that evaluation.
4. Load the deployment model in `POST /api/learner-validation`.
5. Return learner-safe output states and source references without exposing expert recordings or model evidence.

## Boundary

The expert-reference directory supplies the canonical Baybayin recordings used for comparison. The model's error labels come from controlled group attempts, so learner output is labeled preliminary model validation trained on group-protocol attempts and compared against expert reference recordings.

## Deferred

- Expert review of every group attempt and its assigned error label.
- Separate direction and order labels.
- Multi-error training examples and true multi-label error evaluation.
- A frozen expert-labeled held-out dataset for final thesis metrics.
