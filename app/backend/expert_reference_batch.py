"""Checksum-backed import of a reviewed local expert recording batch."""

from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import re

from reference_library import DuplicateReferenceError


_SAFE_FILE = re.compile(r'^[A-Za-z0-9_.-]+\.json$')


def _source_path(root: Path, filename: str) -> Path:
    if not isinstance(filename, str) or not _SAFE_FILE.fullmatch(filename):
        raise ValueError('Manifest contains an unsafe source filename')
    path = (Path(root) / filename).resolve()
    if path.parent != Path(root).resolve():
        raise ValueError('Manifest source is outside the expert-reference directory')
    return path


def _entry_result(entry: dict, source_root: Path, validate_sample, is_current_target) -> tuple[dict, dict | None]:
    result = {'file': entry.get('file'), 'target': entry.get('target'), 'status': 'blocked'}
    try:
        if not isinstance(entry.get('sourceRefs'), list) or not entry['sourceRefs'] or not all(isinstance(value, str) and value for value in entry['sourceRefs']):
            raise ValueError('Manifest entry has no valid source references')
        if not isinstance(entry.get('inputMethod'), str) or not entry['inputMethod']:
            raise ValueError('Manifest entry has no valid input method')
        path = _source_path(source_root, entry.get('file'))
        raw = path.read_bytes()
        expected = entry.get('sha256', '').lower()
        actual = hashlib.sha256(raw).hexdigest()
        if not re.fullmatch(r'[0-9a-f]{64}', expected) or actual != expected:
            raise ValueError('Source file checksum does not match the reviewed manifest')
        parsed = json.loads(raw)
        sample = validate_sample(parsed)
        dumped = sample.model_dump(mode='json') if hasattr(sample, 'model_dump') else sample
        if dumped.get('target') != entry.get('target'):
            raise ValueError('Source target does not match the reviewed manifest')
        if not is_current_target(dumped['target']):
            raise ValueError('Source target is not in the current knowledge graph release')
        result.update({'status': 'ready', 'canvas': dumped['canvas'], 'eventCount': len(dumped['events'])})
        return result, dumped
    except (OSError, ValueError, TypeError, json.JSONDecodeError) as error:
        result['detail'] = str(error)
        return result, None


def preflight_batch(manifest: dict, source_root: Path, validate_sample, is_current_target) -> dict:
    entries = manifest.get('entries')
    if not isinstance(entries, list) or not entries:
        return {'batchId': manifest.get('batchId'), 'ready': False, 'entries': [{'status': 'blocked', 'detail': 'Manifest has no entries'}]}
    seen_files, seen_targets, results = set(), set(), []
    for entry in entries:
        if not isinstance(entry, dict) or entry.get('file') in seen_files or entry.get('target') in seen_targets:
            results.append({'file': entry.get('file') if isinstance(entry, dict) else None, 'target': entry.get('target') if isinstance(entry, dict) else None, 'status': 'blocked', 'detail': 'Manifest contains a duplicate file or target'})
            continue
        seen_files.add(entry.get('file'))
        seen_targets.add(entry.get('target'))
        result, _ = _entry_result(entry, source_root, validate_sample, is_current_target)
        results.append(result)
    return {'batchId': manifest.get('batchId'), 'ready': all(item['status'] == 'ready' for item in results), 'entries': results}


def import_batch(manifest: dict, source_root: Path, repository, validate_sample, is_current_target, importer_code: str) -> dict:
    report = preflight_batch(manifest, source_root, validate_sample, is_current_target)
    if not report['ready']:
        return {**report, 'imported': 0, 'duplicates': 0}
    existing = {record['provenance']['checksum'] for record in repository.list_records()}
    imported = duplicates = 0
    for entry in manifest['entries']:
        _, sample = _entry_result(entry, source_root, validate_sample, is_current_target)
        checksum = repository.checksum(sample)
        if checksum in existing:
            duplicates += 1
            continue
        record = {
            'target': sample['target'], 'sample': sample, 'dataClass': 'reference', 'status': 'candidate',
            'source': {**manifest['source'], 'pages': entry['sourceRefs']},
            'capture': {'inputMethod': entry['inputMethod']},
            'review': {'reviewerCode': 'pending', 'notes': 'Imported from a checksum-verified expert batch; awaiting reviewer confirmation.', 'decisionDate': None, 'specificationVersion': None},
            'provenance': {
                'importedAt': datetime.now(timezone.utc).isoformat(), 'checksum': checksum, 'schemaVersion': 1,
                'expertBatchId': manifest['batchId'], 'expertCode': manifest['expertCode'],
                'sourceFile': entry['file'], 'sourceFileSha256': entry['sha256'].lower(),
                'collectionDate': manifest['collectionDate'], 'sourceCanvas': sample['canvas'], 'importerCode': importer_code,
            },
        }
        try:
            repository.create_record(record)
            existing.add(checksum)
            imported += 1
        except DuplicateReferenceError:
            duplicates += 1
    return {**report, 'imported': imported, 'duplicates': duplicates}
