import pytest

from evaluation_metrics import EvaluationMetricError, binary_metrics, confusion_matrix_by_error


def test_calculates_binary_accuracy_precision_recall_and_f1():
    result = binary_metrics([True, True, False, False], [True, False, True, False])

    assert result == {
        'truePositive': 1, 'falsePositive': 1, 'trueNegative': 1, 'falseNegative': 1,
        'accuracy': 0.5, 'precision': 0.5, 'recall': 0.5, 'f1': 0.5,
    }


def test_handles_zero_positive_predictions_without_division_error():
    result = binary_metrics([True, False], [False, False])

    assert result['precision'] == 0.0
    assert result['recall'] == 0.0
    assert result['f1'] == 0.0


def test_builds_confusion_matrix_for_one_error_category():
    records = [
        {'expertErrors': ['wrong_stroke_direction'], 'predictedErrors': ['wrong_stroke_direction']},
        {'expertErrors': [], 'predictedErrors': ['wrong_stroke_direction']},
        {'expertErrors': ['wrong_stroke_direction'], 'predictedErrors': []},
        {'expertErrors': [], 'predictedErrors': []},
    ]

    result = confusion_matrix_by_error(records, 'wrong_stroke_direction')

    assert result['truePositive'] == 1
    assert result['falsePositive'] == 1
    assert result['falseNegative'] == 1
    assert result['trueNegative'] == 1


def test_rejects_missing_or_non_boolean_binary_labels():
    with pytest.raises(EvaluationMetricError, match='same length'):
        binary_metrics([True], [])
    with pytest.raises(EvaluationMetricError, match='boolean'):
        binary_metrics([1], [True])
