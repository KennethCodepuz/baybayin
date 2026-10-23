import pytest

from scoring import score_form_measurements, score_stroke_measurements


def config():
    return {
        'schemaVersion': 1, 'id': 'ka-v1', 'targetId': 'ka', 'referenceBundleId': 'bundle-ka', 'status': 'approved',
        'approval': {'reviewerCode': 'expert-01', 'decisionDate': '2026-10-23'},
        'algorithms': {
            'stroke': {'version': 'dtw-v1', 'pointCount': 32, 'bandRatio': 0.25, 'maximumNormalizedDistance': 0.2},
            'form': {'version': 'mask-v1', 'minimumIou': 0.8},
        },
    }


def stroke_measurements(distance=0.1):
    return {
        'errors': [], 'referenceStrokeCount': 1, 'learnerStrokeCount': 1,
        'comparisons': [{'strokeIndex': 0, 'comparisonType': 'dtw_path', 'algorithmVersion': 'dtw-v1', 'normalizedDistance': distance}],
    }


def test_scores_only_against_matching_approved_calibration():
    form = score_form_measurements({'maskIou': 0.9}, config(), target_id='ka', reference_bundle_id='bundle-ka')
    stroke = score_stroke_measurements(stroke_measurements(), config(), target_id='ka', reference_bundle_id='bundle-ka')

    assert form['available'] is True and form['passed'] is True
    assert stroke['available'] is True and stroke['passed'] is True
    assert form['evidence']['calibrationId'] == 'ka-v1'


def test_returns_a_specific_failure_without_hiding_structural_errors():
    result = score_stroke_measurements(
        {'errors': ['wrong_stroke_count'], 'referenceStrokeCount': 2, 'learnerStrokeCount': 1, 'comparisons': []}, config(), target_id='ka', reference_bundle_id='bundle-ka'
    )

    assert result['passed'] is False
    assert result['errors'] == ['wrong_stroke_count']


def test_returns_measurement_based_errors_when_thresholds_are_exceeded():
    form = score_form_measurements({'maskIou': 0.5}, config(), target_id='ka', reference_bundle_id='bundle-ka')
    stroke = score_stroke_measurements(
        stroke_measurements(0.3), config(), target_id='ka', reference_bundle_id='bundle-ka'
    )

    assert form['errors'] == ['wrong_form']
    assert stroke['errors'] == ['trajectory_mismatch']


def test_rejects_calibration_for_a_different_target_or_bundle():
    with pytest.raises(ValueError, match='target'):
        score_form_measurements({'maskIou': 1}, config(), target_id='ba', reference_bundle_id='bundle-ka')
    with pytest.raises(ValueError, match='bundle'):
        score_form_measurements({'maskIou': 1}, config(), target_id='ka', reference_bundle_id='bundle-ba')


def test_never_passes_empty_or_non_finite_stroke_evidence():
    result = score_stroke_measurements(
        {'errors': [], 'referenceStrokeCount': 1, 'learnerStrokeCount': 1, 'comparisons': []},
        config(), target_id='ka', reference_bundle_id='bundle-ka',
    )
    assert result['available'] is False
    assert result['passed'] is None
    assert result['errors'] == ['missing_comparison_evidence']

    with pytest.raises(ValueError, match='numeric'):
        score_stroke_measurements(stroke_measurements(float('nan')), config(), target_id='ka', reference_bundle_id='bundle-ka')
