import math

import pytest

from model_training import (
    FEATURE_NAMES,
    ModelTrainingError,
    fit_deterministic_baseline,
    run_leave_one_writer_out,
)


def row(writer, label, offset):
    values = {
        'mask_iou': 0.95 - offset if label == 'conforming' else 0.30 - offset / 10,
        'centroid_distance': 0.02 + offset if label == 'conforming' else 0.35 + offset,
        'ink_width_difference': 0.01 + offset if label == 'conforming' else 0.20 + offset,
        'ink_height_difference': 0.01 + offset if label == 'conforming' else 0.20 + offset,
        'stroke_count_difference': 0.0 if label == 'conforming' else 2.0,
        'stroke_path_distance': 0.02 + offset if label == 'conforming' else 0.50 + offset,
        'path_length_ratio': 1.0 + offset if label == 'conforming' else 1.8 + offset,
        'start_end_displacement': 0.01 + offset if label == 'conforming' else 0.30 + offset,
        'direction_match_ratio': 1.0 if label == 'conforming' else 0.2,
    }
    return {
        'sample_id': f'{writer}_{label}_{offset}', 'writer_code': writer,
        'target': 'a', 'binary_label': label, **values,
    }


def rows():
    return [
        row('W01', 'conforming', 0.001), row('W01', 'non_conforming', 0.001),
        row('W02', 'conforming', 0.002), row('W02', 'non_conforming', 0.002),
        row('W03', 'conforming', 0.003), row('W03', 'non_conforming', 0.003),
    ]


def test_baseline_rejects_missing_or_non_finite_feature_values():
    invalid = rows()[:2]
    invalid[0] = {**invalid[0], 'mask_iou': math.nan}

    with pytest.raises(ModelTrainingError, match='finite'):
        fit_deterministic_baseline(invalid)


def test_writer_disjoint_run_keeps_held_out_writer_out_of_each_training_fold():
    result = run_leave_one_writer_out(rows(), random_seed=17)

    assert result['random_seed'] == 17
    assert len(result['predictions']) == 12
    for fold in result['folds']:
        assert fold['held_out_writer'] not in fold['training_writers']
        assert fold['test_count'] == 2
        assert fold['training_count'] == 4
    assert {prediction['method'] for prediction in result['predictions']} == {'deterministic_baseline', 'random_forest'}
    assert all(prediction['writer_code'] == prediction['held_out_writer'] for prediction in result['predictions'])


def test_fixed_seed_reproduces_random_forest_predictions_and_metrics():
    first = run_leave_one_writer_out(rows(), random_seed=17)
    second = run_leave_one_writer_out(rows(), random_seed=17)

    assert first['predictions'] == second['predictions']
    assert set(first['report']['methods']) == {'deterministic_baseline', 'random_forest'}
    assert FEATURE_NAMES == first['feature_names']
