"""Convert internal validator evidence into a learner-safe practice response."""


def learner_result(preview: dict) -> dict:
    """Never expose templates or claim a score before calibrated scoring exists."""
    has_reference = bool(preview.get('referenceBundleId'))
    if not has_reference:
        return {
            'schemaVersion': 1, 'state': 'unavailable', 'target': preview['targetId'],
            'message': 'Practice comparison is being prepared for this character. Please choose another character or try again later.',
            'form': {'state': 'unavailable'}, 'stroke': {'state': 'unavailable'}, 'hybrid': {'state': 'unavailable'},
            'feedback': {'mode': 'deterministic', 'items': []}, 'sourceRefs': preview.get('sourceRefs', []),
        }
    if preview.get('overall', {}).get('available'):
        passed = preview['overall']['passed']
        errors = [*preview.get('form', {}).get('errors', []), *preview.get('stroke', {}).get('errors', [])]
        return {
            'schemaVersion': 1, 'state': 'prototype_result', 'target': preview['targetId'],
            'message': 'Prototype match' if passed else 'Prototype result: needs more practice',
            'form': {'state': 'pass' if preview['form']['passed'] else 'needs_practice'},
            'stroke': {'state': 'pass' if preview['stroke']['passed'] else 'needs_practice'},
            'hybrid': {'state': 'pass' if passed else 'needs_practice'},
            'feedback': {'mode': 'deterministic', 'items': errors[:3]}, 'sourceRefs': preview.get('sourceRefs', []),
        }
    errors = [*preview.get('form', {}).get('errors', []), *preview.get('stroke', {}).get('errors', [])]
    return {
        'schemaVersion': 1, 'state': 'practice_comparison', 'target': preview['targetId'],
        'message': 'Your drawing was compared for practice. Expert-approved thresholds are still required before this system can judge it correct or incorrect.',
        'form': {'state': 'provisional'}, 'stroke': {'state': 'provisional'}, 'hybrid': {'state': 'provisional'},
        'feedback': {'mode': 'deterministic', 'items': errors[:3]}, 'sourceRefs': preview.get('sourceRefs', []),
    }
