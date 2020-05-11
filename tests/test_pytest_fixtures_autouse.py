import pytest

from requre.storage import PersistentObjectStorage
from tests.testbase import network_connection_avalilable

pytest_plugins = ["requre.pytest_fixtures"]


@pytest.fixture(autouse=True)
def record_requests_fixture_autouse(record_requests_fixture):
    yield record_requests_fixture


@pytest.mark.skipif(not network_connection_avalilable(), reason="No network connection")
def test_record_requests_fixture():
    import requests

    assert (
        PersistentObjectStorage().storage_file.name
        == "test_record_requests_fixture.yaml"
    )
    requests.get("https://google.com")
    assert len(PersistentObjectStorage().storage_object) == 2


@pytest.mark.skipif(not network_connection_avalilable(), reason="No network connection")
def test_record_requests_fixture_different_call():
    import requests

    assert (
        PersistentObjectStorage().storage_file.name
        == "test_record_requests_fixture_different_call.yaml"
    )
    requests.get("https://fedoraproject.org")
    assert len(PersistentObjectStorage().storage_object) == 2
