import pytest

from ai_feedback import FeedbackValidationError, build_ai_request, validate_ai_response


CONTEXT = {
    'target': {'targetId': 'ka', 'label': 'ka'},
    'errors': ['wrong_form'],
    'sourceRefs': ['lopez-2025-pdf#pdf-page=56'],
    'imageReferenceIds': ['core-character-chart-part-2'],
}
RESULT = {'form': {'errors': ['wrong_form']}, 'stroke': {'errors': []}}


def test_builds_a_constrained_ai_explanation_request():
    request = build_ai_request(CONTEXT, RESULT)

    assert request['allowedErrors'] == ['wrong_form']
    assert request['sourceRefs'] == ['lopez-2025-pdf#pdf-page=56']
    assert request['instructions'].startswith('Explain only')


def test_rejects_ai_output_that_invents_errors_or_sources():
    valid = validate_ai_response({
        'message': 'The character form needs correction.',
        'detectedErrors': ['wrong_form'],
        'sourceRefs': ['lopez-2025-pdf#pdf-page=56'],
        'needsReview': False,
    }, CONTEXT, RESULT)
    assert valid['mode'] == 'ai_grounded'

    with pytest.raises(FeedbackValidationError, match='unsupported errors'):
        validate_ai_response({
            'message': 'Bad order.', 'detectedErrors': ['wrong_stroke_order'],
            'sourceRefs': ['lopez-2025-pdf#pdf-page=56'], 'needsReview': False,
        }, CONTEXT, RESULT)