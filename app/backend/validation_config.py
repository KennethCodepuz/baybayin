"""Validation calibration configuration checks.

Configurations are data supplied by qualified reviewers. This module validates
their shape only; it does not decide that a calibration is academically valid.
"""

from __future__ import annotations

from copy import deepcopy
import math


class CalibrationConfigError(ValueError):
    pass


def _required(mapping: dict, key: str):
    value = mapping.get(key)
    if value is None or value == '':
        raise CalibrationConfigError(f'{key} is required')
    return value


def _number(value, field: str, *, minimum: float | None = None, maximum: float | None = None) -> None:
    if not isinstance(value, (int, float)) or isinstance(value, bool):
        raise CalibrationConfigError(f'{field} must be numeric')
    if not math.isfinite(value):
        raise CalibrationConfigError(f'{field} must be finite')
    if minimum is not None and value < minimum:
        raise CalibrationConfigError(f'{field} must be at least {minimum}')
    if maximum is not None and value > maximum:
        raise CalibrationConfigError(f'{field} must be at most {maximum}')


def validate_calibration_config(config: dict) -> dict:
    """Validate an approved per-bundle calibration and return a safe copy."""
    if not isinstance(config, dict):
        raise CalibrationConfigError('Calibration configuration must be an object')
    for field in ('schemaVersion', 'id', 'targetId', 'referenceBundleId', 'status', 'approval', 'algorithms'):
        _required(config, field)
    if config['schemaVersion'] != 1:
        raise CalibrationConfigError('schemaVersion must be 1')
    if config['status'] != 'approved':
        raise CalibrationConfigError('Calibration configuration must be approved before scoring')
    approval = config['approval']
    if not isinstance(approval, dict):
        raise CalibrationConfigError('approval must be an object')
    _required(approval, 'reviewerCode')
    _required(approval, 'decisionDate')
    algorithms = config['algorithms']
    if not isinstance(algorithms, dict):
        raise CalibrationConfigError('algorithms must be an object')
    stroke = _required(algorithms, 'stroke')
    form = _required(algorithms, 'form')
    if not isinstance(stroke, dict) or not isinstance(form, dict):
        raise CalibrationConfigError('stroke and form algorithms must be objects')
    for field in ('version', 'pointCount', 'bandRatio', 'maximumNormalizedDistance'):
        _required(stroke, field)
    for field in ('version', 'minimumIou'):
        _required(form, field)
    if not isinstance(stroke['pointCount'], int) or isinstance(stroke['pointCount'], bool) or stroke['pointCount'] < 2:
        raise CalibrationConfigError('pointCount must be an integer of at least 2')
    _number(stroke['bandRatio'], 'bandRatio', minimum=0.000001, maximum=1)
    _number(stroke['maximumNormalizedDistance'], 'maximumNormalizedDistance', minimum=0)
    _number(form['minimumIou'], 'minimumIou', minimum=0, maximum=1)
    return deepcopy(config)
