import json
import pytest
from ai_provider import AIProviderError, generate_explanation


def request():
    return {'targetId': 'ba', 'allowedErrors': ['wrong_form'], 'sourceRefs': ['source'], 'imageReferenceIds': [], 'validatorResult': {'formErrors': ['wrong_form'], 'strokeErrors': []}, 'instructions': 'Explain only allowed errors.'}


def test_provider_requires_gateway_configuration(monkeypatch):
    monkeypatch.setattr('ai_provider.load_local_env', lambda: None)
    monkeypatch.delenv('AI_GATEWAY_API_KEY', raising=False)
    monkeypatch.delenv('AI_GATEWAY_MODEL', raising=False)
    with pytest.raises(AIProviderError, match='not configured'):
        generate_explanation(request())


def test_provider_sends_safe_context_and_reads_json(monkeypatch):
    monkeypatch.setattr('ai_provider.load_local_env', lambda: None)
    monkeypatch.setenv('AI_GATEWAY_API_KEY', 'test-key')
    monkeypatch.setenv('AI_GATEWAY_MODEL', 'provider/test-model')
    def post(url, **kwargs):
        prompt = json.loads(kwargs['json']['messages'][0]['content'])
        assert prompt['context']['imageReferenceIds'] == []
        assert 'imageData' not in prompt['context']
        assert 'events' not in prompt['context']
        class Response:
            def raise_for_status(self): pass
            def json(self): return {'choices': [{'message': {'content': json.dumps({'message': 'Try the shape again.', 'detectedErrors': ['wrong_form'], 'sourceRefs': ['source'], 'needsReview': False})}}]}
        return Response()
    assert generate_explanation(request(), post=post)['detectedErrors'] == ['wrong_form']


def test_provider_hides_malformed_gateway_response(monkeypatch):
    monkeypatch.setattr('ai_provider.load_local_env', lambda: None)
    monkeypatch.setenv('AI_GATEWAY_API_KEY', 'test-key')
    monkeypatch.setenv('AI_GATEWAY_MODEL', 'provider/test-model')
    class Response:
        def raise_for_status(self): pass
        def json(self): return {'choices': []}
    with pytest.raises(AIProviderError, match='unavailable'):
        generate_explanation(request(), post=lambda *_args, **_kwargs: Response())
