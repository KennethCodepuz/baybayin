"""Source-constrained retrieval and deterministic feedback for validator outcomes."""

from __future__ import annotations

from knowledge_graph import KnowledgeGraph


_ERROR_GUIDANCE = {
    'wrong_form': 'The overall character form does not match the selected reference.',
    'missing_required_region': 'A required part of the character form appears to be missing.',
    'unexpected_mark': 'An extra mark appears outside the expected character form.',
    'out_of_bounds_proportion': 'The character proportions fall outside the approved reference area.',
    'missing_kudlit': 'The expected kudlit is missing.',
    'misplaced_kudlit': 'The kudlit is not in the expected position.',
    'ambiguous_form': 'The character form could not be distinguished reliably.',
    'wrong_stroke_count': 'The recorded number of strokes differs from the approved reference.',
    'wrong_stroke_order': 'The strokes were recorded in a different order from the approved reference.',
    'wrong_stroke_direction': 'At least one stroke direction differs from the approved reference.',
    'wrong_start_region': 'A stroke starts outside its expected region.',
    'wrong_end_region': 'A stroke ends outside its expected region.',
    'trajectory_mismatch': 'A recorded stroke path differs from the approved reference path.',
    'wrong_kudlit_stroke': 'The kudlit stroke differs from the approved reference.',
}
_KUDLIT_TARGETS = {'be', 'bi', 'bo', 'bu'}


def retrieve_feedback_context(graph: KnowledgeGraph, target_id: str, errors: list[str]) -> dict:
    target = graph.find_target(target_id)
    if not target:
        raise ValueError('Unknown knowledge-graph target')
    supported_errors = [error for error in errors if error in _ERROR_GUIDANCE]
    image_reference_ids = (
        ['core-character-chart-part-1', 'kudlit-pamalit-placement-chart']
        if target_id in _KUDLIT_TARGETS
        else ['core-character-chart-part-1']
    )
    return {
        'target': target,
        'errors': supported_errors,
        'sourceRefs': target['sourceRefs'],
        'imageReferenceIds': image_reference_ids,
    }


def deterministic_feedback(context: dict, validation_result: dict) -> dict:
    """Explain only errors supplied by the validator; never infer additional mistakes."""
    branch_errors = [
        *validation_result.get('form', {}).get('errors', []),
        *validation_result.get('stroke', {}).get('errors', []),
    ]
    allowed = [error for error in context['errors'] if error in branch_errors]
    if not allowed:
        message = 'The validator does not have an approved, source-supported mistake to explain yet.'
    else:
        message = ' '.join(_ERROR_GUIDANCE[error] for error in allowed)
    return {
        'schemaVersion': 1,
        'mode': 'deterministic_fallback',
        'targetId': context['target']['targetId'],
        'message': message,
        'detectedErrors': allowed,
        'sourceRefs': context['sourceRefs'],
        'imageReferenceIds': context['imageReferenceIds'],
        'needsReview': not bool(allowed),
    }