import requests
import unittest
from requre.online_replacing import record_requests_for_all_methods


@record_requests_for_all_methods()
class BaseTest(unittest.TestCase):
    def cassette_setup(self, cassette):
        pass
        # do what ever you want with cassette setup

    def test(self):
        response = requests.get("http://example.com")
        self.assertIn("This domain is for use", response.text)
