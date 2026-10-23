"""Deterministic structural checks backed by approved stroke annotations."""

from __future__ import annotations

import math

from stroke_matching import StrokeMatchError, normalize_stroke_sequence


class StructuralRuleError(ValueError):
    pass


def _direction(start: dict, end: dict) -> str:
    dx, dy = end['x'] - start['x'], end['y'] - start['y']
    if abs(dx) < 0.02 and abs(dy) < 0.02:
        return 'stationary'
    if abs(dx) >= abs(dy):
        return 'right' if dx > 0 else 'left'
    return 'down' if dy > 0 else 'up'


def _in_region(point: dict, region: dict) -> bool:
    return region['left'] <= point['x'] <= region['right'] and region['top'] <= point['y'] <= region['bottom']


def _regions(rules: dict, field: str, count: int) -> list[dict] | None:
    regions = rules.get(field)
    if regions is None:
        return None
    if not isinstance(regions, list) or len(regions) != count:
        raise StructuralRuleError(f'{field} must contain one region per expected stroke')
    required = ('left', 'top', 'right', 'bottom')
    for region in regions:
        if not isinstance(region, dict) or any(key not in region for key in required):
            raise StructuralRuleError(f'Each {field} item must be a normalized region')
        for key in required:
            value = region[key]
            if not isinstance(value, (int, float)) or isinstance(value, bool) or not math.isfinite(value) or not 0 <= value <= 1:
                raise StructuralRuleError('Normalized region values must be between 0 and 1')
        if region['left'] > region['right'] or region['top'] > region['bottom']:
            raise StructuralRuleError('Normalized region boundaries must be ordered')
    return regions


def evaluate_structural_strokes(learner_strokes: list[list[dict]], rules: dict, *, target_id: str, reference_bundle_id: str) -> dict:
    """Return approved structural-rule findings without calculating a final score."""
    if not isinstance(rules, dict):
        raise StructuralRuleError('Structural rules must be an object')
    required = ('schemaVersion', 'id', 'targetId', 'referenceBundleId', 'status', 'reviewerCode', 'decisionDate', 'expectedStrokeCount')
    if any(rules.get(field) in (None, '') for field in required):
        raise StructuralRuleError('Approved structural rules require complete approval provenance')
    if rules.get('status') != 'approved':
        raise StructuralRuleError('Structural rules must be approved before use')
    if rules['schemaVersion'] != 1:
        raise StructuralRuleError('Structural rule schemaVersion must be 1')
    if rules['targetId'] != target_id or rules['referenceBundleId'] != reference_bundle_id:
        raise StructuralRuleError('Structural rules must match the target and reference bundle')
    expected_count = rules.get('expectedStrokeCount')
    if not isinstance(expected_count, int) or isinstance(expected_count, bool) or expected_count < 1:
        raise StructuralRuleError('expectedStrokeCount must be a positive integer')
    try:
        normalized = normalize_stroke_sequence(learner_strokes)
    except StrokeMatchError as error:
        raise StructuralRuleError(str(error)) from error
    if len(normalized) != expected_count:
        return {
            'available': True,
            'scored': False,
            'errors': ['wrong_stroke_count'],
            'evidence': {'ruleSource': 'approved_annotation', 'annotationId': rules['id'], 'checks': {'direction': 'not_run_due_to_stroke_count'}},
        }
    expected_directions = rules.get('expectedDirections')
    if expected_directions is not None and (not isinstance(expected_directions, list) or len(expected_directions) != expected_count):
        raise StructuralRuleError('expectedDirections must contain one direction per expected stroke')
    start_regions = _regions(rules, 'startRegions', expected_count)
    end_regions = _regions(rules, 'endRegions', expected_count)
    errors: list[str] = []
    directions = [_direction(stroke[0], stroke[-1]) for stroke in normalized]
    if expected_directions is not None and directions != expected_directions:
        errors.append('wrong_stroke_direction')
    if start_regions and any(not _in_region(stroke[0], region) for stroke, region in zip(normalized, start_regions)):
        errors.append('wrong_start_region')
    if end_regions and any(not _in_region(stroke[-1], region) for stroke, region in zip(normalized, end_regions)):
        errors.append('wrong_end_region')
    return {
        'available': True,
        'scored': False,
        'errors': errors,
        'evidence': {
            'ruleSource': 'approved_annotation', 'annotationId': rules['id'],
            'checks': {'direction': directions, 'startRegion': bool(start_regions), 'endRegion': bool(end_regions)},
        },
    }
