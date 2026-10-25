"""Derive labeled prototype thresholds from supplied accepted practice recordings."""

import json
from pathlib import Path

from form_matching import compare_form_images
from multimodal import extract_stroke_features
from stroke_matching import compare_stroke_sequences


def create_prototype_calibrations(repository, graph, roots, *, decision_date):
    samples = {}
    for root in roots:
        for path in Path(root).glob('*.json'):
            value = json.loads(path.read_text(encoding='utf-8'))
            if graph.is_current_release_target(value.get('target')):
                samples.setdefault(value['target'], []).append(value)
    created = []
    for target_id, values in samples.items():
        bundle = repository.get_active_bundle(target_id)
        if not bundle or len(values) < 2:
            continue
        form_scores, stroke_scores = [], []
        for value in values:
            form_scores.append(compare_form_images(bundle['image']['normalized']['pngDataUrl'], value['image'])['measurements']['maskIou'])
            learner = [stroke['points'] for stroke in extract_stroke_features(value)['strokes']]
            comparison = compare_stroke_sequences([stroke['points'] for stroke in bundle['stroke']['strokes']], learner)
            if comparison['errors']:
                break
            stroke_scores.extend(item['normalizedDistance'] for item in comparison['comparisons'])
        else:
            config = {'schemaVersion': 1, 'id': f'calibration-{target_id}-prototype-v1', 'targetId': target_id, 'referenceBundleId': bundle['id'], 'status': 'approved', 'approval': {'reviewerCode': 'prototype-calibration', 'decisionDate': decision_date}, 'algorithms': {'stroke': {'version': 'dtw-v1', 'pointCount': 32, 'bandRatio': .25, 'maximumNormalizedDistance': max(stroke_scores)}, 'form': {'version': 'mask-v1', 'minimumIou': min(form_scores)}}}
            repository.create_calibration(config)
            created.append(target_id)
    return created
