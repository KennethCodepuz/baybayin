from model_multioutput import (
    OUTPUT_ERROR_CLASSES,
    build_deployment_model,
    evaluate_multioutput_folds,
    validate_multioutput_features,
)
from model_training import FEATURE_NAMES, ModelTrainingError
import pytest


def row(writer, condition, offset, target='a'):
    values = {
        'mask_iou': 0.95 - offset if condition == 'intended_conforming' else 0.25,
        'centroid_distance': 0.02 + offset if condition == 'intended_conforming' else 0.35,
        'ink_width_difference': 0.01 + offset if condition == 'intended_conforming' else 0.20,
        'ink_height_difference': 0.01 + offset if condition == 'intended_conforming' else 0.20,
        'stroke_count_difference': 0.0 if condition != 'wrong_count' else 2.0,
        'stroke_path_distance': 0.02 + offset if condition == 'intended_conforming' else 0.50,
        'path_length_ratio': 1.0 + offset if condition == 'intended_conforming' else 1.8,
        'start_end_displacement': 0.01 + offset if condition == 'intended_conforming' else 0.30,
        'direction_match_ratio': 1.0 if condition != 'wrong_process' else 0.2,
    }
    return {'sample_id': f'{writer}_{target}_{condition}_{offset}', 'writer_code': writer, 'target': target, 'condition': condition, **values}


def rows():
    conditions = ['intended_conforming', 'wrong_form', 'wrong_count', 'wrong_process', 'wrong_kudlit']
    return [row(writer, condition, 0.001 * (index + 1), 'be') for writer in ('W01', 'W02', 'W03') for index, condition in enumerate(conditions)]


def test_multioutput_validation_marks_kudlit_not_applicable_for_plain_target():
    model = build_deployment_model(rows(), random_seed=17)
    result = validate_multioutput_features(model, row('W04', 'intended_conforming', 0.01, 'a'))

    assert set(result['validation']) == set(OUTPUT_ERROR_CLASSES)
    assert result['validation']['kudlit']['state'] == 'not_applicable'
    assert result['overall']['state'] in {'pass', 'needs_practice'}


def test_multioutput_folds_are_writer_disjoint_and_emit_every_applicable_output():
    result = evaluate_multioutput_folds(rows(), random_seed=17)

    assert len(result['folds']) == 3
    assert all(fold['held_out_writer'] not in fold['training_writers'] for fold in result['folds'])
    assert set(result['report']['outputs']) == set(OUTPUT_ERROR_CLASSES)
    assert result['feature_names'] == FEATURE_NAMES


def test_versioned_candidate_requires_matching_feature_version_and_reference_checksum():
    model = build_deployment_model(rows(), random_seed=17)
    model['feature_schema_version'] = 'pilot-centerline-v2'
    model['reference_checksums'] = {'a': 'expected'}
    features = {**row('W04', 'intended_conforming', 0.01), 'feature_schema_version': 'pilot-centerline-v2', 'reference_checksum': 'wrong'}
    with pytest.raises(ModelTrainingError, match='reference'):
        validate_multioutput_features(model, features)
    features['reference_checksum'] = 'expected'
    features['feature_schema_version'] = 'pilot-v1'
    with pytest.raises(ModelTrainingError, match='feature schema'):
        validate_multioutput_features(model, features)
