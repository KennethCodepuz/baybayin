import hashlib
import json
from pathlib import Path
from uuid import uuid4


class DuplicateReferenceError(Exception):
    pass


class ReferenceNotFoundError(Exception):
    pass


class ReferenceRepository:
    """Small local repository for developer-curated reference recordings."""

    def __init__(self, root: Path):
        self.root = Path(root)
        self.records_dir = self.root / 'records'
        self.specifications_dir = self.root / 'specifications'

    @staticmethod
    def checksum(sample: dict) -> str:
        canonical = json.dumps(sample, sort_keys=True, separators=(',', ':')).encode('utf-8')
        return hashlib.sha256(canonical).hexdigest()

    def _ensure_directories(self):
        self.records_dir.mkdir(parents=True, exist_ok=True)
        self.specifications_dir.mkdir(parents=True, exist_ok=True)

    @staticmethod
    def _write_json(path: Path, value: dict):
        temporary = path.with_suffix(f'{path.suffix}.tmp')
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
        self._ensure_directories()
        checksum = record['provenance']['checksum']
        if any(existing['provenance']['checksum'] == checksum for existing in self._records()):
            raise DuplicateReferenceError()
        saved = {**record, 'id': f"ref-{uuid4().hex}"}
        self._write_json(self.records_dir / f"{saved['id']}.json", saved)
        self.write_manifest()
        return saved

    def get_record(self, record_id: str) -> dict:
        path = self.records_dir / f'{record_id}.json'
        if not path.exists():
            raise ReferenceNotFoundError()
        return json.loads(path.read_text(encoding='utf-8'))

    def list_records(self) -> list[dict]:
        return self._records()

    def update_record(self, record: dict) -> dict:
        self._write_json(self.records_dir / f"{record['id']}.json", record)
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
            'specifications': [
                specification for specification in self.list_specifications()
                if specification['status'] == 'approved'
            ],
            'relationships': relationships,
        }

    def write_manifest(self):
        self._ensure_directories()
        self._write_json(self.root / 'manifest.json', self.manifest())
