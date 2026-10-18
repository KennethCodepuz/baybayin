from fastapi.testclient import TestClient
from main import app

client = TestClient(app)


def sample():
    return {
        "version": 1,
        "createdAt": "2026-10-18T00:00:00.000Z",
        "target": "ka",
        "canvas": {"width": 640, "height": 400},
        "image": "data:image/png;base64,aGVsbG8=",
        "events": [
            {"type": "down", "x": 10, "y": 20, "timestamp": 100, "pointerType": "pen"},
            {"type": "move", "x": 20, "y": 30, "timestamp": 110, "pointerType": "pen"},
            {"type": "up", "x": 30, "y": 40, "timestamp": 120, "pointerType": "pen"},
        ],
    }


def test_accepts_and_returns_a_complete_capture():
    payload = sample()
    response = client.post('/api/samples/check', json=payload)
    assert response.status_code == 200
    assert response.json() == {"sample": payload}


def test_rejects_a_blank_target_and_incomplete_stroke():
    payload = sample()
    payload['target'] = '  '
    assert client.post('/api/samples/check', json=payload).status_code == 422
    payload = sample()
    payload['events'].pop()
    assert client.post('/api/samples/check', json=payload).status_code == 422


def test_rejects_impossible_sequence_and_backwards_timestamps():
    payload = sample()
    payload['events'][0]['type'] = 'move'
    assert client.post('/api/samples/check', json=payload).status_code == 422
    payload = sample()
    payload['events'][1]['timestamp'] = 99
    assert client.post('/api/samples/check', json=payload).status_code == 422


def test_rejects_invalid_canvas_and_image():
    payload = sample()
    payload['canvas']['width'] = 0
    assert client.post('/api/samples/check', json=payload).status_code == 422
    payload = sample()
    payload['image'] = 'not an image'
    assert client.post('/api/samples/check', json=payload).status_code == 422
