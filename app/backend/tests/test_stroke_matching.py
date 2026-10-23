import pytest

from stroke_matching import (
    StrokeMatchError,
    compare_stroke_sequences,
    constrained_dtw,
    normalize_stroke_sequence,
    resample_by_arc_length,
)


def line(start, end, points=3):
    return [
        {
            'x': start['x'] + (end['x'] - start['x']) * index / (points - 1),
            'y': start['y'] + (end['y'] - start['y']) * index / (points - 1),
        }
        for index in range(points)
    ]


def test_arc_length_resampling_preserves_endpoints_and_count():
    source = [{'x': 0.0, 'y': 0.0}, {'x': 0.2, 'y': 0.0}, {'x': 1.0, 'y': 0.0}]

    result = resample_by_arc_length(source, 5)

    assert len(result) == 5
    assert result[0] == source[0]
    assert result[-1] == source[-1]
    assert result[2] == {'x': 0.5, 'y': 0.0}


def test_glyph_normalization_removes_translation_and_uniform_scale():
    reference = [line({'x': 0, 'y': 0}, {'x': 10, 'y': 0}), line({'x': 10, 'y': 0}, {'x': 10, 'y': 5})]
    translated_and_scaled = [line({'x': 100, 'y': 30}, {'x': 140, 'y': 30}), line({'x': 140, 'y': 30}, {'x': 140, 'y': 50})]

    assert normalize_stroke_sequence(reference) == normalize_stroke_sequence(translated_and_scaled)


def test_dtw_treats_dense_and_sparse_samples_of_same_path_as_similar():
    sparse = line({'x': 0, 'y': 0}, {'x': 1, 'y': 1}, 3)
    dense = line({'x': 0, 'y': 0}, {'x': 1, 'y': 1}, 15)

    result = constrained_dtw(sparse, dense, band_ratio=1.0)

    assert result['normalizedDistance'] < 0.2
    assert result['alignmentPath'][0] == [0, 0]
    assert result['alignmentPath'][-1] == [len(sparse) - 1, len(dense) - 1]


def test_reversed_path_has_higher_distance_than_matching_path():
    reference = line({'x': 0, 'y': 0}, {'x': 1, 'y': 0}, 5)

    matching = constrained_dtw(reference, reference, band_ratio=1.0)
    reversed_path = constrained_dtw(reference, list(reversed(reference)), band_ratio=1.0)

    assert matching['normalizedDistance'] == pytest.approx(0.0)
    assert reversed_path['normalizedDistance'] > matching['normalizedDistance']


def test_compares_each_ordered_stroke_and_reports_count_mismatch_without_scoring():
    reference = [
        line({'x': 0, 'y': 0}, {'x': 1, 'y': 0}),
        line({'x': 1, 'y': 0}, {'x': 1, 'y': 1}),
    ]
    learner = [line({'x': 0, 'y': 0}, {'x': 1, 'y': 0}, 7)]

    result = compare_stroke_sequences(reference, learner, point_count=8, band_ratio=0.5)

    assert result['available'] is True
    assert result['scored'] is False
    assert result['errors'] == ['wrong_stroke_count']
    assert result['comparisons'] == []


def test_comparison_uses_normalized_resampled_paths_without_mutating_inputs():
    reference = [line({'x': 0, 'y': 0}, {'x': 10, 'y': 10})]
    learner = [line({'x': 20, 'y': 40}, {'x': 60, 'y': 80}, 9)]
    original_reference = [[point.copy() for point in stroke] for stroke in reference]
    original_learner = [[point.copy() for point in stroke] for stroke in learner]

    result = compare_stroke_sequences(reference, learner, point_count=16, band_ratio=0.5)

    assert result['errors'] == []
    assert result['comparisons'][0]['normalizedDistance'] == pytest.approx(0.0)
    assert reference == original_reference
    assert learner == original_learner


def test_rejects_invalid_alignment_and_degenerate_path_input():
    with pytest.raises(StrokeMatchError, match='band ratio'):
        constrained_dtw([{'x': 0, 'y': 0}], [{'x': 0, 'y': 0}], band_ratio=0)
    with pytest.raises(StrokeMatchError, match='at least two'):
        resample_by_arc_length([{'x': 0, 'y': 0}], 4)


def test_compares_stationary_dot_strokes_without_sending_them_to_dtw():
    path = line({'x': 0, 'y': 0}, {'x': 1, 'y': 0})
    dot = [{'x': 0.5, 'y': 0.6}, {'x': 0.5, 'y': 0.6}]

    result = compare_stroke_sequences([path, dot], [path, dot])

    assert result['errors'] == []
    assert result['comparisons'][0]['comparisonType'] == 'dtw_path'
    assert result['comparisons'][1] == {
        'strokeIndex': 1, 'comparisonType': 'dot_position', 'normalizedDistance': 0.0,
    }


def test_measures_displaced_stationary_dot_position():
    path = line({'x': 0, 'y': 0}, {'x': 1, 'y': 0})
    reference_dot = [{'x': 0.2, 'y': 0.5}, {'x': 0.2, 'y': 0.5}]
    learner_dot = [{'x': 0.8, 'y': 0.5}, {'x': 0.8, 'y': 0.5}]

    result = compare_stroke_sequences([path, reference_dot], [path, learner_dot])

    assert result['comparisons'][1]['comparisonType'] == 'dot_position'
    assert result['comparisons'][1]['normalizedDistance'] > 0
