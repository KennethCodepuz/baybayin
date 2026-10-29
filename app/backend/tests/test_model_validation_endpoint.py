from fastapi.testclient import TestClient
import base64
import io
from PIL import Image, ImageDraw

import main


client = TestClient(main.app)


def sample():
    image = Image.new('RGB', (20, 20), 'white')
    ImageDraw.Draw(image).line((2, 2, 18, 18), fill='black', width=2)
    output = io.BytesIO()
    image.save(output, format='PNG')
    return {
        'version': 1, 'createdAt': '2026-10-28T00:00:00.000Z', 'target': 'a',
        'canvas': {'width': 2, 'height': 2},
        'image': 'data:image/png;base64,' + base64.b64encode(output.getvalue()).decode('ascii'),
        'events': [
            {'type': 'down', 'x': 0, 'y': 0, 'timestamp': 0, 'pointerType': 'pen'},
            {'type': 'up', 'x': 1, 'y': 1, 'timestamp': 1, 'pointerType': 'pen'},
        ],
    }


def test_learner_endpoint_uses_preliminary_multioutput_model(monkeypatch):
    monkeypatch.setattr(main, 'validate_sample_with_model', lambda *_: {
        'schemaVersion': 1, 'state': 'preliminary_model_validation', 'target': 'a',
        'message': 'Preliminary model validation complete.',
        'validation': {
            'form': {'state': 'pass', 'confidence': 0.1},
            'count': {'state': 'needs_practice', 'confidence': 0.8},
            'process': {'state': 'pass', 'confidence': 0.2},
            'kudlit': {'state': 'not_applicable', 'confidence': None},
        },
        'overall': {'state': 'needs_practice', 'detected': ['count']}, 'evidence': {}, 'limitation': 'Preliminary model validation only.',
    })

    response = client.post('/api/learner-validation', json=sample())

    assert response.status_code == 200
    assert response.json()['state'] == 'preliminary_model_validation'
    assert response.json()['validation']['count']['state'] == 'needs_practice'
    assert response.json()['sourceRefs']
