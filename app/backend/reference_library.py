import hashlib
import json
from pathlib import Path
import re
import threading
from uuid import uuid4


class DuplicateReferenceError(Exception):
    pass


class ReferenceNotFoundError(Exception):
    pass


class InvalidReferenceIdentifierError(ValueError):
    pass


class ReferenceRepository:
    """Small local repository for developer-curated reference recordings."""

    def __init__(self, root: Path):
        self.root = Path(root)
        self.records_dir = self.root / 'records'
        self.specifications_dir = self.root / 'specifications'
        self.bundles_dir = self.root / 'bundles'
        self.active_bundles_path = self.root / 'active-bundles.json'
        self._lock = threading.RLock()

    @staticmethod
    def _identifier(value: str, pattern: str) -> str:
        if not isinstance(value, str) or not re.fullmatch(pattern, value):
            raise InvalidReferenceIdentifierError('Invalid reference-library identifier')
        return value

    def _path(self, directory: Path, identifier: str, pattern: str) -> Path:
        safe = self._identifier(identifier, pattern)
        path = (directory / f'{safe}.json').resolve()
        if path.parent != directory.resolve():
            raise InvalidReferenceIdentifierError('Invalid reference-library identifier')
        return path

    @staticmethod
    def checksum(sample: dict) -> str:
        canonical = json.dumps(sample, sort_keys=True, separators=(',', ':')).encode('utf-8')
        return hashlib.sha256(canonical).hexdigest()

    def _ensure_directories(self):
        self.records_dir.mkdir(parents=True, exist_ok=True)
        self.specifications_dir.mkdir(parents=True, exist_ok=True)
        self.bundles_dir.mkdir(parents=True, exist_ok=True)

    @staticmethod
    def _write_json(path: Path, value: dict):
        temporary = path.with_suffix(f'{path.suffix}.{uuid4().hex}.tmp')
        temporary.write_text(json.dumps(value, indent=2, ensure_ascii=True), encoding='utf-8')
        temporary.replace(path)

    def _records(self) -> list[dict]:
        if not self.records_dir.exists():
            return []
        return sorted(
            (json.loads(path.read_text(encoding='utf-8')) for path in self.records_dir.glob('*.json')),
            key=lambda record: record['provenance']['importedAt'],
        )

    def create_record(self, record: dict) -> dict:
        with self._lock:
            self._ensure_directories()
            checksum = record['provenance']['checksum']
            if any(existing['provenance']['checksum'] == checksum for existing in self._records()):
                raise DuplicateReferenceError()
            saved = {**record, 'id': f"ref-{uuid4().hex}"}
            self._write_json(self._path(self.records_dir, saved['id'], r'ref-[0-9a-f]{32}'), saved)
            self.write_manifest()
            return saved

    def get_record(self, record_id: str) -> dict:
        path = self._path(self.records_dir, record_id, r'ref-[0-9a-f]{32}')
        if not path.exists():
            raise ReferenceNotFoundError()
        return json.loads(path.read_text(encoding='utf-8'))

    def list_records(self) -> list[dict]:
        return self._records()

    def update_record(self, record: dict) -> dict:
        with self._lock:
            self._write_json(self._path(self.records_dir, record['id'], r'ref-[0-9a-f]{32}'), record)
            self.write_manifest()
            return record

    def create_specification(self, specification: dict) -> dict:
        self._ensure_directories()
        path = self.specifications_dir / f"{specification['target']}--{specification['version']}.json"
        if path.exists():
            raise DuplicateReferenceError()
        self._write_json(path, specification)
        self.write_manifest()
        return specification

    def get_specification(self, target: str, version: str) -> dict | None:
        path = self.specifications_dir / f'{target}--{version}.json'
        if not path.exists():
            return None
        return json.loads(path.read_text(encoding='utf-8'))

    def list_specifications(self) -> list[dict]:
        if not self.specifications_dir.exists():
            return []
        return sorted(
            (json.loads(path.read_text(encoding='utf-8')) for path in self.specifications_dir.glob('*.json')),
            key=lambda specification: (specification['target'], specification['version']),
        )

    def create_bundle(self, bundle: dict) -> dict:
        self._ensure_directories()
        path = self.bundles_dir / f"{bundle['id']}.json"
        if path.exists():
            raise DuplicateReferenceError()
        self._write_json(path, bundle)
        self.write_manifest()
        return bundle

    def get_bundle(self, bundle_id: str) -> dict | None:
        path = self._path(self.bundles_dir, bundle_id, r'bundle-[A-Za-z0-9._-]+')
        if not path.exists():
            return None
        return json.loads(path.read_text(encoding='utf-8'))

    def active_bundle_registry(self) -> dict:
        if not self.active_bundles_path.exists():
            return {'schemaVersion': 1, 'targets': {}}
        return json.loads(self.active_bundles_path.read_text(encoding='utf-8'))

    def activate_bundle(self, target_id: str, bundle_id: str, reviewer_code: str, decision_date: str, reason: str) -> dict:
        self._ensure_directories()
        bundle = self.get_bundle(bundle_id)
        if not bundle or bundle.get('targetId') != target_id or bundle.get('status') != 'approved':
            raise ReferenceNotFoundError()
        record = self.get_record(bundle['referenceRecordId'])
        if record.get('status') != 'approved':
            raise ReferenceNotFoundError()
        registry = self.active_bundle_registry()
        current = registry['targets'].get(target_id, {'history': []})
        history = [*current.get('history', []), {
            'bundleId': bundle_id,
            'reviewerCode': reviewer_code,
            'decisionDate': decision_date,
            'reason': reason,
        }]
        registry['targets'][target_id] = {'bundleId': bundle_id, 'history': history}
        self._write_json(self.active_bundles_path, registry)
        return registry['targets'][target_id]

    def get_active_bundle(self, target_id: str) -> dict | None:
        active = self.active_bundle_registry()['targets'].get(target_id)
        if not active:
            return None
        bundle = self.get_bundle(active.get('bundleId'))
        if not bundle or bundle.get('targetId') != target_id or bundle.get('status') != 'approved':
            return None
        try:
            record = self.get_record(bundle['referenceRecordId'])
        except ReferenceNotFoundError:
            return None
        return bundle if record.get('status') == 'approved' else None

    def list_bundles(self) -> list[dict]:
        if not self.bundles_dir.exists():
            return []
        return sorted(
            (json.loads(path.read_text(encoding='utf-8')) for path in self.bundles_dir.glob('*.json')),
            key=lambda bundle: bundle['id'],
        )

    def manifest(self) -> dict:
        records = [
            record for record in self._records()
            if record['dataClass'] == 'reference' and record['status'] == 'approved'
        ]
        relationships = []
        for record in records:
            relationships.append({'from': record['id'], 'type': 'represents', 'to': f"character:{record['target']}"})
            version = record['review'].get('specificationVersion')
            if version:
                relationships.append({
                    'from': record['id'], 'type': 'reviewedAgainst',
                    'to': f"specification:{record['target']}:{version}",
                })
        return {
            'version': 1,
            'records': records,
            'bundles': self.list_bundles(),
            'specifications': [
                specification for specification in self.list_specifications()
                if specification['status'] == 'approved'
            ],
            'relationships': relationships,
        }

    def write_manifest(self):
        self._ensure_directories()
        self._write_json(self.root / 'manifest.json', self.manifest())
