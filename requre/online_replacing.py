# Copyright Contributors to the Packit project.
# SPDX-License-Identifier: MIT

from requre.helpers import record_requests as _record_requests
from requre.helpers import recording_requests as _recording_requests
from requre.record_and_replace import (
    apply_decorator_to_all_methods as _apply_decorator_to_all_methods,
)
from requre.record_and_replace import record as _record
from requre.record_and_replace import recording as _recording
from requre.record_and_replace import replace

# BACKWARDS COMPATIBILITY
recording = _recording
record = _record
replace_module_match = replace
record_requests = _record_requests
record_requests_for_all_methods = record_requests
recording_requests = _recording_requests
apply_decorator_to_all_methods = _apply_decorator_to_all_methods
