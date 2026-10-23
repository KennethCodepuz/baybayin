import base64
import io
from datetime import date

import pytest
from PIL import Image
from fastapi.testclient import TestClient

from main import app


def png_data_url():
    image = Image.new('RGB', (2, 2), 'white')
    output = io.BytesIO()
    image.save(output, format='PNG')
    return 'data:image/png;base64,' + base64.b64encode(output.getvalue()).decode('ascii')


def sample(target='ba'):
    return {
        'version': 1,
        'createdAt': '2026-10-20T00:00:00.000Z',
        'target': target,
        'canvas': {'width': 640, 'height': 400},
        'image': png_data_url(),
        'events': [
            {'type': 'down', 'x': 10, 'y': 20, 'timestamp': 100, 'pointerType': 'pen'},
            {'type': 'up', 'x': 10, 'y': 20, 'timestamp': 110, 'pointerType': 'pen'},
        ],
    }


@pytest.fixture
def client(tmp_path):
    from reference_library import ReferenceRepository

    app.state.reference_repository = ReferenceRepository(tmp_path / 'reference-library')
    with TestClient(app) as test_client:
        yield test_client


def candidate_payload(target='ba'):
    return {
        'sample': sample(target),
        'dataClass': 'reference',
        'source': {'title': 'Pagsulat ng Baybayin', 'pages': ['7'], 'convention': 'pinagyamang-baybayin'},
        'capture': {'inputMethod': 'pen'},
        'review': {'reviewerCode': 'pending', 'notes': 'Awaiting expert review.'},
    }


def test_creates_and_lists_a_candidate_without_changing_the_sample(client):
    payload = candidate_payload()
    response = client.post('/api/references', json=payload)

    assert response.status_code == 201
    record = response.json()['record']
    assert record['status'] == 'candidate'
    assert record['dataClass'] == 'reference'
    assert record['target'] == 'ba'
    assert record['sample'] == payload['sample']
    assert record['provenance']['checksum']
    assert client.get('/api/references').json()['records'] == [record]


def test_rejects_duplicates_and_accepts_core_graph_targets(client):
    assert client.post('/api/references', json=candidate_payload()).status_code == 201
    assert client.post('/api/references', json=candidate_payload()).status_code == 409
    assert client.post('/api/references', json=candidate_payload('nga')).status_code == 201


def test_requires_an_approved_matching_specification_before_approval(client):
    record = client.post('/api/references', json=candidate_payload()).json()['record']
    review = {'status': 'approved', 'reviewerCode': 'expert-01', 'decisionDate': str(date.today()), 'notes': 'Approved.'}
    assert client.patch(f"/api/references/{record['id']}/review", json=review).status_code == 422

    specification = {
        'target': 'ba', 'version': 'ba-1.0', 'status': 'approved',
        'source': {'title': 'Pagsulat ng Baybayin', 'pages': ['7'], 'convention': 'pinagyamang-baybayin'},
        'reviewerCode': 'expert-01', 'decisionDate': str(date.today()),
    }
    response = client.post('/api/specifications', json=specification)
    assert response.status_code == 201

    review['specificationVersion'] = 'ba-1.0'
    response = client.patch(f"/api/references/{record['id']}/review", json=review)
    assert response.status_code == 200
    assert response.json()['record']['status'] == 'approved'
    assert response.json()['record']['review']['specificationVersion'] == 'ba-1.0'


def test_manifest_excludes_test_and_rejected_records_by_default(client):
    approved = client.post('/api/references', json=candidate_payload()).json()['record']
    client.post('/api/specifications', json={
        'target': 'ba', 'version': 'ba-1.0', 'status': 'approved',
        'source': {'title': 'Pagsulat ng Baybayin', 'pages': ['7'], 'convention': 'pinagyamang-baybayin'},
        'reviewerCode': 'expert-01', 'decisionDate': str(date.today()),
    })
    client.patch(f"/api/references/{approved['id']}/review", json={
        'status': 'approved', 'reviewerCode': 'expert-01', 'decisionDate': str(date.today()),
        'notes': 'Approved.', 'specificationVersion': 'ba-1.0',
    })

    test_record = client.post('/api/references', json={**candidate_payload('ka'), 'dataClass': 'test'}).json()['record']
    client.patch(f"/api/references/{test_record['id']}/review", json={
        'status': 'rejected', 'reviewerCode': 'developer-01', 'decisionDate': str(date.today()), 'notes': 'Fixture only.',
    })

    manifest = client.get('/api/references/manifest').json()
    assert [record['id'] for record in manifest['records']] == [approved['id']]
    assert manifest['relationships'] == [
        {'from': approved['id'], 'type': 'represents', 'to': 'character:ba'},
        {'from': approved['id'], 'type': 'reviewedAgainst', 'to': 'specification:ba:ba-1.0'},
    ]
