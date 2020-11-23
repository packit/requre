import pytest

from tests.testbase import network_connection_available

pytest_plugins = ["requre.pytest_fixtures"]


@pytest.fixture(autouse=True)
def record_requests_fixture_autouse(record_requests_fixture):
    yield record_requests_fixture


@pytest.mark.skipif(not network_connection_available(), reason="No network connection")
def test_record_requests_fixture():
    import requests

    requests.get("https://google.com")


@pytest.mark.skipif(not network_connection_available(), reason="No network connection")
def test_record_requests_fixture_different_call():
    import requests

    requests.get("https://fedoraproject.org")
