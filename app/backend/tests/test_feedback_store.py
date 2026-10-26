from feedback_store import FeedbackResultStore


def test_store_returns_only_short_lived_server_issued_context():
    store = FeedbackResultStore()
    token = store.put({'targetId': 'ba', 'form': {'errors': ['wrong_form']}})
    assert store.get(token)['targetId'] == 'ba'
    assert store.get('browser-supplied-id') is None
