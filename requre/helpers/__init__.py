# Copyright Contributors to the Packit project.
# SPDX-License-Identifier: MIT

"""
This file is used by users to import special recording decorators or context managers.

* Can contain pre-made helpers for modules/functions with side effects.
* Can contain helpers consisting from multiple replacements
  so user can have only one for a group of related replacements that are always used together.
"""

from requre.helpers.git.helper import record_git_module
from requre.helpers.requests_response import record_requests, recording_requests
from requre.helpers.tempfile import record_tempfile_module

__all__ = [
    record_requests.__name__,
    recording_requests.__name__,
    record_tempfile_module.__name__,
    record_git_module.__name__,
]
