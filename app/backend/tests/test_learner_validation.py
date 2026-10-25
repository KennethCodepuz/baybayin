from learner_validation import learner_result


def test_learner_result_hides_private_bundle_and_never_scores_a_provisional_comparison():
    result = learner_result({
        'targetId': 'ba', 'referenceBundleId': 'bundle-private-id',
        'form': {'errors': [], 'available': False}, 'stroke': {'errors': [], 'available': False},
        'sourceRefs': ['lopez-2025-pdf#pdf-page=56'],
    })

    assert result['state'] == 'practice_comparison'
    assert result['form']['state'] == 'provisional'
    assert result['feedback']['items'] == []
    assert 'referenceBundleId' not in result
    assert 'passed' not in str(result).lower()


def test_learner_result_reports_unavailable_without_a_reference_bundle():
    result = learner_result({
        'targetId': 'ba', 'referenceBundleId': None,
        'form': {'errors': []}, 'stroke': {'errors': []}, 'sourceRefs': [],
    })

    assert result['state'] == 'unavailable'
    assert result['form']['state'] == 'unavailable'
