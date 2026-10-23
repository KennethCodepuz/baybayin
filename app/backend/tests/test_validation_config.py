import pytest

from validation_config import CalibrationConfigError, validate_calibration_config


def approved_config():
    return {
        'schemaVersion': 1,
        'id': 'ka-v1-calibration',
        'targetId': 'ka',
        'referenceBundleId': 'bundle-ref-ka-ka-1.0',
        'status': 'approved',
        'approval': {'reviewerCode': 'expert-01', 'decisionDate': '2026-10-23'},
        'algorithms': {
            'stroke': {'version': 'dtw-v1', 'pointCount': 32, 'bandRatio': 0.2, 'maximumNormalizedDistance': 0.25},
            'form': {'version': 'mask-v1', 'minimumIou': 0.7},
        },
    }


def test_accepts_a_complete_approved_calibration_with_provenance():
    config = validate_calibration_config(approved_config())

    assert config['id'] == 'ka-v1-calibration'
    assert config['algorithms']['stroke']['pointCount'] == 32


@pytest.mark.parametrize('field', ['referenceBundleId', 'approval'])
def test_rejects_missing_required_provenance(field):
    config = approved_config()
    del config[field]

    with pytest.raises(CalibrationConfigError, match='required'):
        validate_calibration_config(config)


def test_rejects_unapproved_or_invalid_dtw_configuration():
    provisional = approved_config()
    provisional['status'] = 'provisional'
    with pytest.raises(CalibrationConfigError, match='approved'):
        validate_calibration_config(provisional)

    invalid_dtw = approved_config()
    invalid_dtw['algorithms']['stroke']['bandRatio'] = 1.5
    with pytest.raises(CalibrationConfigError, match='bandRatio'):
        validate_calibration_config(invalid_dtw)
