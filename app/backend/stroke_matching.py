"""Pure, non-scoring DTW utilities for ordered handwriting strokes."""

from __future__ import annotations

import math
from copy import deepcopy


class StrokeMatchError(ValueError):
    """Raised when a stroke path cannot be compared reproducibly."""


def _point(point: dict) -> dict[str, float]:
    if not isinstance(point, dict):
        raise StrokeMatchError('Each point must be an object with x and y coordinates')
    x, y = point.get('x'), point.get('y')
    if not isinstance(x, (int, float)) or isinstance(x, bool) or not isinstance(y, (int, float)) or isinstance(y, bool):
        raise StrokeMatchError('Each point must have numeric x and y coordinates')
    if not math.isfinite(x) or not math.isfinite(y):
        raise StrokeMatchError('Each point must have finite x and y coordinates')
    return {'x': float(x), 'y': float(y)}


def _validated_stroke(points: list[dict]) -> list[dict[str, float]]:
    if not isinstance(points, list) or len(points) < 2:
        raise StrokeMatchError('Each stroke must contain at least two points')
    return [_point(point) for point in points]


def _distance(left: dict, right: dict) -> float:
    return math.dist((left['x'], left['y']), (right['x'], right['y']))


def _is_dot(points: list[dict]) -> bool:
    return all(_distance(points[0], point) == 0 for point in points[1:])


def resample_by_arc_length(points: list[dict], point_count: int) -> list[dict[str, float]]:
    """Return evenly spaced points along one path while preserving endpoints."""
    source = _validated_stroke(points)
    if not isinstance(point_count, int) or isinstance(point_count, bool) or point_count < 2:
        raise StrokeMatchError('Resampling requires at least two output points')
    segment_lengths = [_distance(start, end) for start, end in zip(source, source[1:])]
    total_length = sum(segment_lengths)
    if total_length == 0:
        raise StrokeMatchError('A stroke path must contain at least two distinct points')

    result = [deepcopy(source[0])]
    segment_index = 0
    completed_length = 0.0
    for output_index in range(1, point_count - 1):
        target_length = total_length * output_index / (point_count - 1)
        while segment_index < len(segment_lengths) - 1 and completed_length + segment_lengths[segment_index] < target_length:
            completed_length += segment_lengths[segment_index]
            segment_index += 1
        segment_length = segment_lengths[segment_index]
        ratio = (target_length - completed_length) / segment_length
        start, end = source[segment_index], source[segment_index + 1]
        result.append({
            'x': round(start['x'] + (end['x'] - start['x']) * ratio, 12),
            'y': round(start['y'] + (end['y'] - start['y']) * ratio, 12),
        })
    result.append(deepcopy(source[-1]))
    return result


def normalize_stroke_sequence(strokes: list[list[dict]]) -> list[list[dict[str, float]]]:
    """Normalize a glyph's strokes together for translation and uniform scale."""
    if not isinstance(strokes, list) or not strokes:
        raise StrokeMatchError('A stroke sequence must contain at least one stroke')
    validated = [_validated_stroke(stroke) for stroke in strokes]
    all_points = [point for stroke in validated for point in stroke]
    minimum_x = min(point['x'] for point in all_points)
    minimum_y = min(point['y'] for point in all_points)
    maximum_x = max(point['x'] for point in all_points)
    maximum_y = max(point['y'] for point in all_points)
    scale = max(maximum_x - minimum_x, maximum_y - minimum_y)
    if scale == 0:
        return [[{'x': 0.5, 'y': 0.5} for point in stroke] for stroke in validated]
    return [
        [
            {
                'x': round((point['x'] - minimum_x) / scale, 12),
                'y': round((point['y'] - minimum_y) / scale, 12),
            }
            for point in stroke
        ]
        for stroke in validated
    ]


def constrained_dtw(reference_points: list[dict], learner_points: list[dict], band_ratio: float = 0.25) -> dict:
    """Calculate DTW distance with a diagonal alignment band and auditable path."""
    if not isinstance(band_ratio, (int, float)) or isinstance(band_ratio, bool) or not 0 < band_ratio <= 1:
        raise StrokeMatchError('DTW band ratio must be greater than 0 and at most 1')
    reference = _validated_stroke(reference_points)
    learner = _validated_stroke(learner_points)
    reference_length, learner_length = len(reference), len(learner)
    band = max(abs(reference_length - learner_length), math.ceil(max(reference_length, learner_length) * float(band_ratio)))
    costs = [[math.inf] * (learner_length + 1) for _ in range(reference_length + 1)]
    parents: dict[tuple[int, int], tuple[int, int]] = {}
    costs[0][0] = 0.0

    for reference_index in range(1, reference_length + 1):
        low = max(1, reference_index - band)
        high = min(learner_length, reference_index + band)
        for learner_index in range(low, high + 1):
            predecessors = (
                (costs[reference_index - 1][learner_index], (reference_index - 1, learner_index)),
                (costs[reference_index][learner_index - 1], (reference_index, learner_index - 1)),
                (costs[reference_index - 1][learner_index - 1], (reference_index - 1, learner_index - 1)),
            )
            prior_cost, parent = min(predecessors, key=lambda candidate: candidate[0])
            if math.isfinite(prior_cost):
                costs[reference_index][learner_index] = _distance(reference[reference_index - 1], learner[learner_index - 1]) + prior_cost
                parents[(reference_index, learner_index)] = parent

    total_cost = costs[reference_length][learner_length]
    if not math.isfinite(total_cost):
        raise StrokeMatchError('DTW alignment cannot fit within the configured band ratio')
    path: list[list[int]] = []
    current = (reference_length, learner_length)
    while current != (0, 0):
        path.append([current[0] - 1, current[1] - 1])
        current = parents[current]
    path.reverse()
    return {
        'algorithmVersion': 'dtw-v1',
        'bandRatio': float(band_ratio),
        'totalCost': round(total_cost, 12),
        'normalizedDistance': round(total_cost / len(path), 12),
        'alignmentPath': path,
    }


def compare_stroke_sequences(
    reference_strokes: list[list[dict]],
    learner_strokes: list[list[dict]],
    *,
    point_count: int = 32,
    band_ratio: float = 0.25,
) -> dict:
    """Compare ordered strokes and return measurement evidence without a correctness score."""
    reference = normalize_stroke_sequence(reference_strokes)
    learner = normalize_stroke_sequence(learner_strokes)
    if len(reference) != len(learner):
        return {
            'available': True,
            'scored': False,
            'algorithmVersion': 'dtw-v1',
            'errors': ['wrong_stroke_count'],
            'comparisons': [],
            'referenceStrokeCount': len(reference),
            'learnerStrokeCount': len(learner),
        }
    comparisons = []
    for index, (reference_stroke, learner_stroke) in enumerate(zip(reference, learner)):
        reference_is_dot = _is_dot(reference_stroke)
        learner_is_dot = _is_dot(learner_stroke)
        if reference_is_dot and learner_is_dot:
            comparisons.append({
                'strokeIndex': index,
                'comparisonType': 'dot_position',
                'normalizedDistance': round(_distance(reference_stroke[0], learner_stroke[0]), 12),
            })
            continue
        if reference_is_dot or learner_is_dot:
            return {
                'available': True,
                'scored': False,
                'algorithmVersion': 'dtw-v1',
                'errors': ['trajectory_mismatch'],
                'comparisons': comparisons,
                'referenceStrokeCount': len(reference),
                'learnerStrokeCount': len(learner),
            }
        comparison = constrained_dtw(
            resample_by_arc_length(reference_stroke, point_count),
            resample_by_arc_length(learner_stroke, point_count),
            band_ratio,
        )
        comparisons.append({'strokeIndex': index, 'comparisonType': 'dtw_path', **comparison})
    return {
        'available': True,
        'scored': False,
        'algorithmVersion': 'dtw-v1',
        'errors': [],
        'comparisons': comparisons,
        'referenceStrokeCount': len(reference),
        'learnerStrokeCount': len(learner),
    }
