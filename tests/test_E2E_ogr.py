import os
import unittest

from ogr import GithubService

from requre.helpers.requests_response import (
    RequestResponseHandling,
    remove_password_from_url,
)
from requre.online_replacing import replace_module_match, record_requests
from requre.cassette import StorageMode, Cassette


class GithubTests(unittest.TestCase):
    def _pr_comments_test(self):
        token = os.environ.get("GITHUB_TOKEN")
        cassette = Cassette()
        if cassette.mode == StorageMode.write and (not token):
            raise EnvironmentError(
                f"You are in Requre write mode, please set proper GITHUB_TOKEN"
                f" env variables {cassette.storage_file}"
            )
        # possible to check before reading values because in other case values are removed
        # and in write mode is does have sense at the end
        if cassette.mode == StorageMode.read:
            self.assertIn(self.id(), cassette.storage_file)
            self.assertIn("LGTM", str(cassette.storage_object))
            self.assertTrue(
                cassette.storage_object["requests.sessions"]["send"]["GET"][
                    "https://api.github.com:443/repos/packit-service/ogr"
                ]
            )
        service = GithubService(token=token)
        ogr_project = service.get_project(namespace="packit-service", repo="ogr")
        pr_comments = ogr_project.get_pr_comments(9)
        assert pr_comments
        assert len(pr_comments) == 2

        assert pr_comments[0].body.endswith("fixed")
        assert pr_comments[1].body.startswith("LGTM")

    @replace_module_match(
        what="requests.sessions.Session.request",
        decorate=RequestResponseHandling.decorator(
            item_list=["method", "url"],
            map_function_to_item={"url": remove_password_from_url},
        ),
    )
    def test_pr_comments(self):
        self._pr_comments_test()

    @record_requests
    def test_pr_comments_record_requests_decorator(self):
        self._pr_comments_test()
