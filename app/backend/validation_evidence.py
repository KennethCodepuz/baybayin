"""Build pending, inspectable validation evidence from an approved reference bundle."""

from __future__ import annotations

from form_matching import compare_form_images
from multimodal import extract_stroke_features, unavailable_branch_result
from kudlit_rules import evaluate_kudlit
from stroke_matching import compare_stroke_sequences


def provisional_bundle_evidence(sample: dict, bundle: dict, source_refs: list[str], annotation: dict | None = None) -> dict:
    """Compare a sample to a bundle while explicitly withholding uncalibrated scores."""
    reference_strokes = [stroke['points'] for stroke in bundle['stroke']['strokes']]
    learner_features = extract_stroke_features(sample)
    learner_strokes = [stroke['points'] for stroke in learner_features['strokes']]
    stroke_measurements = compare_stroke_sequences(reference_strokes, learner_strokes)
    form_measurements = compare_form_images(bundle['image']['normalized']['pngDataUrl'], sample['image'])
    form = unavailable_branch_result('form', 'expert_thresholds_pending', source_refs)
    stroke = unavailable_branch_result('stroke', 'expert_thresholds_pending', source_refs)
    form['evidence'].append({'code': 'provisional_measurements', 'measurements': form_measurements['measurements']})
    stroke['evidence'].append({'code': 'provisional_measurements', 'measurements': stroke_measurements})
    if annotation:
        kudlit = evaluate_kudlit(learner_features['strokes'], annotation, target_id=bundle['targetId'], reference_bundle_id=bundle['id'])
        stroke['errors'].extend(kudlit['errors'])
        stroke['evidence'].append({'code': 'provisional_kudlit', **kudlit['evidence']})
    return {'form': form, 'stroke': stroke}
