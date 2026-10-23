"""Calibration-gated adapters from deterministic measurements to branch results."""

from __future__ import annotations

import math

from validation_config import validate_calibration_config


def _matching_calibration(config: dict, target_id: str, reference_bundle_id: str) -> dict:
    approved = validate_calibration_config(config)
    if approved['targetId'] != target_id:
        raise ValueError('Calibration target does not match the validation target')
    if approved['referenceBundleId'] != reference_bundle_id:
        raise ValueError('Calibration bundle does not match the reference bundle')
    return approved


def _evidence(config: dict) -> dict:
    return {
        'calibrationId': config['id'],
        'referenceBundleId': config['referenceBundleId'],
        'approval': config['approval'],
    }


def score_form_measurements(measurements: dict, config: dict, *, target_id: str, reference_bundle_id: str) -> dict:
    """Score mask overlap only when a matching expert-approved calibration exists."""
    approved = _matching_calibration(config, target_id, reference_bundle_id)
    mask_iou = measurements.get('maskIou') if isinstance(measurements, dict) else None
    if not isinstance(mask_iou, (int, float)) or isinstance(mask_iou, bool) or not math.isfinite(mask_iou) or not 0 <= mask_iou <= 1:
        raise ValueError('Form measurements must include numeric maskIou')
    minimum_iou = approved['algorithms']['form']['minimumIou']
    passed = mask_iou >= minimum_iou
    return {
        'available': True,
        'passed': passed,
        'errors': [] if passed else ['wrong_form'],
        'evidence': {**_evidence(approved), 'algorithmVersion': approved['algorithms']['form']['version'], 'maskIou': mask_iou, 'minimumIou': minimum_iou},
        'sourceRefs': [],
        'branch': 'form',
    }


def score_stroke_measurements(measurements: dict, config: dict, *, target_id: str, reference_bundle_id: str) -> dict:
    """Score DTW evidence while preserving pre-DTW structural error findings."""
    approved = _matching_calibration(config, target_id, reference_bundle_id)
    if not isinstance(measurements, dict):
        raise ValueError('Stroke measurements must be an object')
    errors = list(measurements.get('errors', []))
    comparisons = measurements.get('comparisons', [])
    if not isinstance(comparisons, list):
        raise ValueError('Stroke comparisons must be a list')
    reference_count = measurements.get('referenceStrokeCount')
    learner_count = measurements.get('learnerStrokeCount')
    if not isinstance(reference_count, int) or not isinstance(learner_count, int) or reference_count < 1 or learner_count < 1:
        raise ValueError('Stroke measurements must include positive reference and learner stroke counts')
    if not errors and (reference_count != learner_count or len(comparisons) != reference_count):
        return {'available': False, 'passed': None, 'errors': ['missing_comparison_evidence'], 'evidence': {**_evidence(approved)}, 'sourceRefs': [], 'branch': 'stroke'}
    indices = [item.get('strokeIndex') for item in comparisons if isinstance(item, dict)]
    distances = [item.get('normalizedDistance') for item in comparisons if isinstance(item, dict)]
    if len(indices) != len(comparisons) or sorted(indices) != list(range(len(comparisons))):
        raise ValueError('Stroke comparisons must have consecutive stroke indices')
    if any(not isinstance(distance, (int, float)) or isinstance(distance, bool) or not math.isfinite(distance) or distance < 0 for distance in distances):
        raise ValueError('Each stroke comparison must include numeric normalizedDistance')
    maximum = approved['algorithms']['stroke']['maximumNormalizedDistance']
    if not errors and any(distance > maximum for distance in distances):
        errors.append('trajectory_mismatch')
    return {
        'available': True,
        'passed': not errors,
        'errors': errors,
        'evidence': {
            **_evidence(approved),
            'algorithmVersion': approved['algorithms']['stroke']['version'],
            'maximumNormalizedDistance': maximum,
            'strokeDistances': distances,
        },
        'sourceRefs': [],
        'branch': 'stroke',
    }
