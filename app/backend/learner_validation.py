"""Convert internal validator evidence into a learner-safe practice response."""


def _practice_response(
    preview: dict,
    *,
    state: str,
    message: str,
    branch_state: str,
    errors: list[str],
) -> dict:
    return {
        'schemaVersion': 1,
        'state': state,
        'target': preview['targetId'],
        'message': message,
        'form': {'state': branch_state},
        'stroke': {'state': branch_state},
        'hybrid': {'state': branch_state},
        'feedback': {'mode': 'deterministic', 'items': errors[:3]},
        'sourceRefs': preview.get('sourceRefs', []),
    }


def learner_result(preview: dict) -> dict:
    """Never expose templates or claim a score before calibrated scoring exists."""
    errors = [
        *preview.get('form', {}).get('errors', []),
        *preview.get('stroke', {}).get('errors', []),
    ]
    if not preview.get('referenceBundleId'):
        return _practice_response(
            preview,
            state='unavailable',
            message='Practice comparison is being prepared for this character. Please choose another character or try again later.',
            branch_state='unavailable',
            errors=[],
        )

    if preview.get('overall', {}).get('available'):
        passed = preview['overall']['passed']
        return {
            **_practice_response(
                preview,
                state='prototype_result',
                message='Prototype match' if passed else 'Prototype result: needs more practice',
                branch_state='pass' if passed else 'needs_practice',
                errors=errors,
            ),
            'form': {'state': 'pass' if preview['form']['passed'] else 'needs_practice'},
            'stroke': {'state': 'pass' if preview['stroke']['passed'] else 'needs_practice'},
        }

    return _practice_response(
        preview,
        state='practice_comparison',
        message='Your drawing was compared for practice. Expert-approved thresholds are still required before this system can judge it correct or incorrect.',
        branch_state='provisional',
        errors=errors,
    )
