import os
from requre.storage import PersistentObjectStorage
from requre.helpers.requests_response import RequestResponseHandling
from requre.import_system import upgrade_import_system

upgrade_import_system().decorate(
    where="^requests$",
    what="Session.send",
    who_name=["github"],
    decorator=RequestResponseHandling.decorator_plain,
)

PersistentObjectStorage().storage_file = "github2.yaml"

import github

g = github.Github(os.getenv("TOKEN", "EMPTY"))
print("Count of your repos: ", len(list(g.get_user().get_repos())))

PersistentObjectStorage().dump()
