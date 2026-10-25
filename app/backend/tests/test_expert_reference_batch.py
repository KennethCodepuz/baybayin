import base64
import hashlib
import io
import json

from PIL import Image

from expert_reference_batch import import_batch, preflight_batch
from reference_library import ReferenceRepository


def sample(target='ba'):
    image = Image.new('RGB', (2, 2), 'white')
    output = io.BytesIO()
    image.save(output, format='PNG')
    return {
        'version': 1, 'createdAt': '2026-10-24T00:00:00.000Z', 'target': target,
        'canvas': {'width': 600, 'height': 450},
        'image': 'data:image/png;base64,' + base64.b64encode(output.getvalue()).decode(),
        'events': [
            {'type': 'down', 'x': 1, 'y': 1, 'timestamp': 1, 'pointerType': 'mouse'},
            {'type': 'up', 'x': 1, 'y': 1, 'timestamp': 2, 'pointerType': 'mouse'},
        ],
    }


def manifest_for(source_root, target='ba'):
    raw = json.dumps(sample(target)).encode()
    (source_root / 'expert_ba.json').write_bytes(raw)
    return {
        'batchId': 'expert-batch-test', 'expertCode': 'expert-test', 'collectionDate': '2026-10-24',
        'source': {'title': 'Professional Baybayin reference', 'convention': 'pinagyamang-baybayin'},
        'entries': [{'file': 'expert_ba.json', 'target': target, 'sha256': hashlib.sha256(raw).hexdigest(), 'inputMethod': 'mouse', 'sourceRefs': ['lopez-2025-pdf#pdf-page=56']}],
    }


def test_preflight_validates_before_any_library_write(tmp_path):
    source_root = tmp_path / 'sources'
    source_root.mkdir()
    manifest = manifest_for(source_root)
    report = preflight_batch(manifest, source_root, lambda value: value, lambda target: target == 'ba')

    assert report['ready'] is True
    assert report['entries'][0]['status'] == 'ready'

    manifest['entries'][0]['sha256'] = '0' * 64
    blocked = preflight_batch(manifest, source_root, lambda value: value, lambda target: target == 'ba')
    assert blocked['ready'] is False
    assert blocked['entries'][0]['status'] == 'blocked'


def test_import_is_idempotent_and_preserves_original_sample(tmp_path):
    source_root = tmp_path / 'sources'
    source_root.mkdir()
    manifest = manifest_for(source_root)
    original = (source_root / 'expert_ba.json').read_bytes()
    repository = ReferenceRepository(tmp_path / 'library')
    validator = lambda value: value

    report = import_batch(manifest, source_root, repository, validator, lambda target: target == 'ba', 'developer-01')
    saved = repository.list_records()

    assert report['ready'] is True
    assert report['imported'] == 1
    assert len(saved) == 1
    assert saved[0]['sample'] == sample()
    assert saved[0]['provenance']['expertBatchId'] == 'expert-batch-test'
    assert saved[0]['provenance']['sourceFileSha256'] == hashlib.sha256(original).hexdigest()
    assert (source_root / 'expert_ba.json').read_bytes() == original
    assert import_batch(manifest, source_root, repository, validator, lambda target: target == 'ba', 'developer-01')['duplicates'] == 1


def test_blocked_preflight_creates_no_partial_candidates(tmp_path):
    source_root = tmp_path / 'sources'
    source_root.mkdir()
    manifest = manifest_for(source_root)
    manifest['entries'].append({
        'file': 'missing.json', 'target': 'be', 'sha256': '0' * 64,
        'inputMethod': 'mouse', 'sourceRefs': ['lopez-2025-pdf#pdf-page=56'],
    })
    repository = ReferenceRepository(tmp_path / 'library')

    report = import_batch(manifest, source_root, repository, lambda value: value, lambda target: target in {'ba', 'be'}, 'developer-01')

    assert report['ready'] is False
    assert report['imported'] == 0
    assert repository.list_records() == []
