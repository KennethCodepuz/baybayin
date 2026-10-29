"""Experimental centerline and glyph-normalized position features."""

import math

from centerline_matching import compare_centerlines
from multimodal import extract_stroke_features
from stroke_matching import normalize_stroke_sequence


def normalized_endpoint_displacement(reference_strokes: list[dict], learner_strokes: list[dict]) -> float:
    reference = normalize_stroke_sequence([stroke['points'] for stroke in reference_strokes])
    learner = normalize_stroke_sequence([stroke['points'] for stroke in learner_strokes])
    pairs = list(zip(reference, learner))
    if not pairs:
        raise ValueError('Endpoint comparison needs at least one stroke')
    gaps = []
    for left, right in pairs:
        gaps.append(sum(math.dist((left[i]['x'], left[i]['y']), (right[i]['x'], right[i]['y'])) for i in (0, -1)) / 2)
    return sum(gaps) / len(gaps)


def robust_measurements(reference: dict, learner: dict) -> dict[str, float]:
    ref_strokes = extract_stroke_features(reference)['strokes']
    learner_strokes = extract_stroke_features(learner)['strokes']
    centerline = compare_centerlines(reference['image'], learner['image'])
    return {
        'centerline_distance': centerline['symmetric_distance'],
        'reference_to_learner_distance': centerline['reference_to_learner'],
        'learner_to_reference_distance': centerline['learner_to_reference'],
        'normalized_endpoint_displacement': normalized_endpoint_displacement(ref_strokes, learner_strokes),
    }
