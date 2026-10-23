import pytest
from fastapi import HTTPException

from reference_library import InvalidReferenceIdentifierError, ReferenceRepository
from security import require_reference_token


def test_private_reference_token_rejects_missing_and_invalid_values(monkeypatch):
    monkeypatch.setenv('BAYBAYIN_REFERENCE_TOKEN', 'test-secret')
    with pytest.raises(HTTPException, match='required') as missing:
        require_reference_token(None)
    assert missing.value.status_code == 401
    with pytest.raises(HTTPException, match='rejected') as invalid:
        require_reference_token('Bearer wrong')
    assert invalid.value.status_code == 403
    assert require_reference_token('Bearer test-secret') is None


def test_repository_rejects_windows_path_traversal(tmp_path):
    repository = ReferenceRepository(tmp_path / 'references')
    with pytest.raises(InvalidReferenceIdentifierError):
        repository.get_record('..\\active-bundles')
    with pytest.raises(InvalidReferenceIdentifierError):
        repository.get_bundle('../active-bundles')
