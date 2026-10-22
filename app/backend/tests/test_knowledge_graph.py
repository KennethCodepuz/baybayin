from fastapi.testclient import TestClient
from datetime import date

from main import app
from reference_library import ReferenceRepository


def sample(target):
    return {
        'version': 1,
        'createdAt': '2026-10-22T00:00:00.000Z',
        'target': target,
        'canvas': {'width': 640, 'height': 400},
        'image': 'data:image/png;base64,aGVsbG8=',
        'events': [
            {'type': 'down', 'x': 10, 'y': 20, 'timestamp': 100, 'pointerType': 'pen'},
            {'type': 'up', 'x': 10, 'y': 20, 'timestamp': 110, 'pointerType': 'pen'},
        ],
    }


def candidate_payload(target):
    return {
        'sample': sample(target),
        'dataClass': 'reference',
        'source': {'title': 'Lopez 2025', 'pages': ['56'], 'convention': 'pinagyamang-baybayin'},
        'capture': {'inputMethod': 'pen'},
        'review': {'reviewerCode': 'pending', 'notes': 'Awaiting expert review.'},
    }


def test_catalog_serves_only_the_24_core_targets_with_source_references():
    with TestClient(app) as client:
        response = client.get('/api/knowledge-graph/catalog')

    assert response.status_code == 200
    catalog = response.json()
    assert catalog['sourceId'] == 'lopez-2025-pdf'
    assert len(catalog['targets']) == 24
    assert catalog['targets'][0]['id'] == 'vowel-a'
    assert catalog['targets'][5]['id'] == 'consonant-ba'
    assert catalog['targets'][5]['sourceRefs'] == ['lopez-2025-pdf#pdf-page=56']
    assert catalog['targets'][5]['scoringAvailable'] is False


def test_target_and_readiness_are_read_only_and_unknown_targets_are_not_found(tmp_path):
    app.state.reference_repository = ReferenceRepository(tmp_path / 'reference-library')
    with TestClient(app) as client:
        target = client.get('/api/knowledge-graph/targets/consonant-ba')
        unknown = client.get('/api/knowledge-graph/targets/no-such-target')
        readiness = client.get('/api/knowledge-graph/readiness')

    assert target.status_code == 200
    assert target.json()['target']['readiness'] == 'awaiting_candidate'
    assert unknown.status_code == 404
    assert len(readiness.json()['targets']) == 24
    assert all(item['scoringAvailable'] is False for item in readiness.json()['targets'])


def test_reference_library_accepts_core_graph_targets_but_not_out_of_release_extensions(tmp_path):
    app.state.reference_repository = ReferenceRepository(tmp_path / 'reference-library')
    with TestClient(app) as client:
        core = client.post('/api/references', json=candidate_payload('nga'))
        extension = client.post('/api/references', json=candidate_payload('phonetic-sha'))

    assert core.status_code == 201
    assert core.json()['record']['target'] == 'nga'
    assert extension.status_code == 422


def test_test_data_does_not_count_toward_reference_readiness(tmp_path):
    app.state.reference_repository = ReferenceRepository(tmp_path / 'reference-library')
    payload = candidate_payload('nga')
    payload['dataClass'] = 'test'
    with TestClient(app) as client:
        assert client.post('/api/references', json=payload).status_code == 201
        readiness = client.get('/api/knowledge-graph/targets/nga').json()['target']['readiness']

    assert readiness == 'awaiting_candidate'


def test_readiness_requires_an_approved_record_and_matching_specification(tmp_path):
    app.state.reference_repository = ReferenceRepository(tmp_path / 'reference-library')
    with TestClient(app) as client:
        record = client.post('/api/references', json=candidate_payload('nga')).json()['record']
        assert client.get('/api/knowledge-graph/targets/nga').json()['target']['readiness'] == 'awaiting_expert_approval'
        client.post('/api/specifications', json={
            'target': 'nga', 'version': 'nga-1.0', 'status': 'approved',
            'source': {'title': 'Lopez 2025', 'pages': ['56'], 'convention': 'pinagyamang-baybayin'},
            'reviewerCode': 'expert-01', 'decisionDate': str(date.today()),
        })
        client.patch(f"/api/references/{record['id']}/review", json={
            'status': 'approved', 'reviewerCode': 'expert-01', 'decisionDate': str(date.today()),
            'notes': 'Approved.', 'specificationVersion': 'nga-1.0',
        })

        result = client.get('/api/knowledge-graph/targets/nga')

    assert result.json()['target']['readiness'] == 'reference_ready'
    assert result.json()['target']['scoringAvailable'] is False
