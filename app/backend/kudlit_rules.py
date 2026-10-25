"""Approved, canvas-relative deterministic rules for Baybayin marks."""

import math


class KudlitRuleError(ValueError):
    pass


def _region(region):
    if not isinstance(region, dict) or set(region) != {'left', 'top', 'right', 'bottom'}:
        raise KudlitRuleError('Each mark region must have left, top, right, and bottom')
    if any(not isinstance(region[key], (int, float)) or isinstance(region[key], bool) or not math.isfinite(region[key]) or not 0 <= region[key] <= 1 for key in region):
        raise KudlitRuleError('Mark region values must be finite normalized coordinates')
    if region['left'] > region['right'] or region['top'] > region['bottom']:
        raise KudlitRuleError('Mark region boundaries must be ordered')


def validate_kudlit_annotation(annotation, *, target_id, reference_bundle_id):
    if not isinstance(annotation, dict) or annotation.get('schemaVersion') != 1 or annotation.get('status') != 'approved':
        raise KudlitRuleError('Kudlit annotation must be approved schema version 1')
    if annotation.get('targetId') != target_id or annotation.get('referenceBundleId') != reference_bundle_id:
        raise KudlitRuleError('Kudlit annotation must match the target and active bundle')
    for field in ('id', 'reviewerCode', 'decisionDate', 'expectedStrokeCount'):
        if annotation.get(field) in (None, ''):
            raise KudlitRuleError('Kudlit annotation requires approval provenance and expected stroke count')
    count = annotation['expectedStrokeCount']
    if not isinstance(count, int) or isinstance(count, bool) or count < 1:
        raise KudlitRuleError('expectedStrokeCount must be a positive integer')
    mark = annotation.get('mark')
    if mark is None:
        return None
    if not isinstance(mark, dict) or mark.get('kind') not in {'dot', 'horizontal_line', 'slanted_line'} or mark.get('position') not in {'above', 'below'}:
        raise KudlitRuleError('Mark kind and position must be approved values')
    indices, regions = mark.get('strokeIndices'), mark.get('regions')
    if not isinstance(indices, list) or not indices or len(indices) != len(set(indices)) or any(not isinstance(index, int) or index < 0 or index >= count for index in indices):
        raise KudlitRuleError('Mark stroke indices must be unique expected stroke indices')
    if not isinstance(regions, list) or len(regions) != len(indices):
        raise KudlitRuleError('Each mark stroke needs one expected region')
    for region in regions:
        _region(region)
    return mark


def evaluate_kudlit(strokes, annotation, *, target_id, reference_bundle_id):
    mark = validate_kudlit_annotation(annotation, target_id=target_id, reference_bundle_id=reference_bundle_id)
    if mark is None:
        return {'available': True, 'errors': [], 'evidence': {'state': 'not_applicable'}}
    if len(strokes) != annotation['expectedStrokeCount']:
        return {'available': True, 'errors': [], 'evidence': {'state': 'not_evaluated_due_to_stroke_count'}}
    errors = []
    for index, region in zip(mark['strokeIndices'], mark['regions']):
        stroke = strokes[index]
        box = stroke['boundingBox']
        center = {'x': (box['left'] + box['right']) / 2, 'y': (box['top'] + box['bottom']) / 2}
        inside = region['left'] <= center['x'] <= region['right'] and region['top'] <= center['y'] <= region['bottom']
        if not inside and 'misplaced_kudlit' not in errors:
            errors.append('misplaced_kudlit')
    return {'available': True, 'errors': errors, 'evidence': {'state': 'evaluated', 'kind': mark['kind'], 'position': mark['position']}}
