import pytest

from robust_features import normalized_endpoint_displacement


def stroke(points):
    return {'points': [{'x': x, 'y': y} for x, y in points]}


def test_endpoint_displacement_ignores_whole_symbol_translation_and_scale():
    reference = [stroke([(0.1, 0.2), (0.4, 0.7)]), stroke([(0.2, 0.1), (0.3, 0.1)])]
    shifted = [stroke([(x['x'] * 2 + 0.2, x['y'] * 2 + 0.1) for x in s['points']]) for s in reference]

    assert normalized_endpoint_displacement(reference, shifted) == pytest.approx(0)


def test_endpoint_displacement_preserves_relative_mark_changes():
    reference = [stroke([(0.1, 0.2), (0.4, 0.7)]), stroke([(0.2, 0.1), (0.3, 0.1)])]
    displaced_mark = [reference[0], stroke([(0.2, 0.8), (0.3, 0.8)])]

    assert normalized_endpoint_displacement(reference, displaced_mark) > 0
