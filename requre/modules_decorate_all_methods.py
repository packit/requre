# Copyright Contributors to the Packit project.
# SPDX-License-Identifier: MIT

from requre.helpers.git.helper import record_git_module as _record_git_module
from requre.helpers.tempfile import record_tempfile_module as _record_tempfile_module
from requre.online_replacing import (
    record_requests_for_all_methods,
)

# BACKWARDS COMPATIBILITY
record_requests_module = record_requests_for_all_methods
record_tempfile_module = _record_tempfile_module
record_git_module = _record_git_module
