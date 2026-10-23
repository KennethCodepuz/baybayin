import pytest

from main import app
from security import require_reference_token


@pytest.fixture(autouse=True)
def allow_reference_library_for_existing_tests(request):
    if request.node.get_closest_marker('auth_enabled'):
        yield
        return
    app.dependency_overrides[require_reference_token] = lambda: None
    yield
    app.dependency_overrides.clear()
