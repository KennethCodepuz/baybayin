"""Server-side AI Gateway adapter for explanation only."""

import json
import os
from pathlib import Path

import httpx


class AIProviderError(ValueError):
    pass


def load_local_env():
    path = Path(__file__).with_name('.env')
    if not path.exists():
        return
    for line in path.read_text(encoding='utf-8').splitlines():
        if '=' in line and not line.lstrip().startswith('#'):
            key, value = line.split('=', 1)
            os.environ.setdefault(key.strip(), value.strip())


def generate_explanation(request: dict, *, post=httpx.post) -> dict:
    load_local_env()
    key, model = os.getenv('AI_GATEWAY_API_KEY'), os.getenv('AI_GATEWAY_MODEL')
    if not key or not model:
        raise AIProviderError('AI Gateway is not configured')
    prompt = {
        'role': 'Baybayin feedback explainer', 'rules': request['instructions'],
        'context': {key: request[key] for key in ('targetId', 'allowedErrors', 'sourceRefs', 'imageReferenceIds', 'validatorResult')},
        'output': 'Return JSON with message, detectedErrors, sourceRefs, and needsReview only.',
    }
    try:
        response = post('https://ai-gateway.vercel.sh/v1/chat/completions', headers={'Authorization': f'Bearer {key}'}, json={'model': model, 'messages': [{'role': 'system', 'content': json.dumps(prompt)}], 'temperature': 0.2, 'max_tokens': 180}, timeout=8)
        response.raise_for_status()
        return json.loads(response.json()['choices'][0]['message']['content'])
    except (httpx.HTTPError, KeyError, IndexError, TypeError, json.JSONDecodeError) as error:
        raise AIProviderError('AI explanation is unavailable') from error
