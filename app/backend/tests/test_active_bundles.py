from reference_library import ReferenceRepository


def record(record_id='ref-ka', status='approved'):
    return {
        'id': record_id, 'target': 'ka', 'dataClass': 'reference', 'status': status,
        'review': {'specificationVersion': 'ka-1.0'},
        'provenance': {'checksum': record_id, 'importedAt': '2026-10-23T00:00:00+00:00'},
    }


def bundle(bundle_id='bundle-ka-1', record_id='ref-ka'):
    return {'id': bundle_id, 'targetId': 'ka', 'referenceRecordId': record_id, 'status': 'approved'}


def test_bundle_requires_explicit_activation_before_it_is_resolved(tmp_path):
    repository = ReferenceRepository(tmp_path / 'references')
    stored = repository.create_record(record())
    repository.create_bundle(bundle(record_id=stored['id']))

    assert repository.get_active_bundle('ka') is None

    activated = repository.activate_bundle('ka', 'bundle-ka-1', 'expert-01', '2026-10-23', 'Selected after review.')

    assert activated['bundleId'] == 'bundle-ka-1'
    assert repository.get_active_bundle('ka')['id'] == 'bundle-ka-1'


def test_activation_keeps_history_and_replaces_the_previous_active_bundle(tmp_path):
    repository = ReferenceRepository(tmp_path / 'references')
    first = repository.create_record(record())
    second = repository.create_record(record('ref-ka-2'))
    repository.create_bundle(bundle(record_id=first['id']))
    repository.create_bundle(bundle('bundle-ka-2', second['id']))
    repository.activate_bundle('ka', 'bundle-ka-1', 'expert-01', '2026-10-23', 'Initial selection.')

    repository.activate_bundle('ka', 'bundle-ka-2', 'expert-02', '2026-10-24', 'Replaced after review.')

    active = repository.active_bundle_registry()['targets']['ka']
    assert active['bundleId'] == 'bundle-ka-2'
    assert [entry['bundleId'] for entry in active['history']] == ['bundle-ka-1', 'bundle-ka-2']
    assert repository.get_bundle('bundle-ka-1')['status'] == 'approved'


def test_does_not_resolve_an_active_bundle_when_its_reference_is_superseded(tmp_path):
    repository = ReferenceRepository(tmp_path / 'references')
    stored_record = repository.create_record(record())
    repository.create_bundle(bundle(record_id=stored_record['id']))
    repository.activate_bundle('ka', 'bundle-ka-1', 'expert-01', '2026-10-23', 'Selected after review.')
    stored_record['status'] = 'superseded'
    repository.update_record(stored_record)

    assert repository.get_active_bundle('ka') is None
