"""Provider-neutral safety contract for future AI feedback generation."""

from __future__ import annotations


class FeedbackValidationError(ValueError):
    pass


def build_ai_request(context: dict, validation_result: dict) -> dict:
    errors = list(context['errors'])
    return {
        'targetId': context['target']['targetId'],
        'allowedErrors': errors,
        'sourceRefs': list(context['sourceRefs']),
        'imageReferenceIds': list(context['imageReferenceIds']),
        'validatorResult': {
            'formErrors': list(validation_result.get('form', {}).get('errors', [])),
            'strokeErrors': list(validation_result.get('stroke', {}).get('errors', [])),
        },
        'instructions': 'Explain only the allowed errors. Do not decide correctness, add errors, or cite sources outside the supplied list.',
    }


def validate_ai_response(response: dict, context: dict, validation_result: dict) -> dict:
    if not isinstance(response, dict) or not isinstance(response.get('message'), str) or not response['message'].strip():
        raise FeedbackValidationError('AI feedback must include a message')
    allowed_errors = set(context['errors'])
    actual_errors = set(validation_result.get('form', {}).get('errors', [])) | set(validation_result.get('stroke', {}).get('errors', []))
    errors = response.get('detectedErrors')
    references = response.get('sourceRefs')
    if not isinstance(errors, list) or not set(errors).issubset(allowed_errors & actual_errors):
        raise FeedbackValidationError('AI feedback contains unsupported errors')
    if not isinstance(references, list) or not set(references).issubset(set(context['sourceRefs'])):
        raise FeedbackValidationError('AI feedback contains unsupported sources')
    return {
        'schemaVersion': 1,
        'mode': 'ai_grounded',
        'targetId': context['target']['targetId'],
        'message': response['message'].strip(),
        'detectedErrors': errors,
        'sourceRefs': references,
        'needsReview': bool(response.get('needsReview')),
    }