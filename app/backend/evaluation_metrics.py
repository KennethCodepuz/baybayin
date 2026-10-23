"""Pure metrics for expert-labeled held-out evaluation records."""

from __future__ import annotations


class EvaluationMetricError(ValueError):
    pass


def binary_metrics(expected: list[bool], predicted: list[bool]) -> dict:
    if not isinstance(expected, list) or not isinstance(predicted, list) or len(expected) != len(predicted):
        raise EvaluationMetricError('Expected and predicted labels must have the same length')
    if not expected:
        raise EvaluationMetricError('At least one label is required')
    if any(type(value) is not bool for value in [*expected, *predicted]):
        raise EvaluationMetricError('Binary labels must be boolean')
    true_positive = sum(actual and result for actual, result in zip(expected, predicted))
    false_positive = sum(not actual and result for actual, result in zip(expected, predicted))
    true_negative = sum(not actual and not result for actual, result in zip(expected, predicted))
    false_negative = sum(actual and not result for actual, result in zip(expected, predicted))
    precision = true_positive / (true_positive + false_positive) if true_positive + false_positive else 0.0
    recall = true_positive / (true_positive + false_negative) if true_positive + false_negative else 0.0
    return {
        'truePositive': true_positive,
        'falsePositive': false_positive,
        'trueNegative': true_negative,
        'falseNegative': false_negative,
        'accuracy': (true_positive + true_negative) / len(expected),
        'precision': precision,
        'recall': recall,
        'f1': 2 * precision * recall / (precision + recall) if precision + recall else 0.0,
    }


def confusion_matrix_by_error(records: list[dict], error_code: str) -> dict:
    if not isinstance(records, list) or not error_code:
        raise EvaluationMetricError('Evaluation records and an error code are required')
    expected, predicted = [], []
    for record in records:
        if not isinstance(record, dict) or 'expertErrors' not in record or 'predictedErrors' not in record:
            raise EvaluationMetricError('Each evaluation record needs expertErrors and predictedErrors')
        expert_errors, predicted_errors = record['expertErrors'], record['predictedErrors']
        if not isinstance(expert_errors, list) or not isinstance(predicted_errors, list):
            raise EvaluationMetricError('Error labels must be lists')
        expected.append(error_code in expert_errors)
        predicted.append(error_code in predicted_errors)
    return binary_metrics(expected, predicted)
