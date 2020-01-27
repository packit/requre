import os
from requre.storage import PersistentObjectStorage
from requre.helpers.requests_response import RequestResponseHandling
import requests

requests.Session.send = RequestResponseHandling.decorator_plain(requests.Session.send)

PersistentObjectStorage().storage_file = "github.yaml"

import github

g = github.Github(os.getenv("TOKEN", "EMPTY"))
print("Count of your repos: ", len(list(g.get_user().get_repos())))

PersistentObjectStorage().dump()
