# MIT License
#
# Copyright (c) 2018-2019 Red Hat, Inc.

# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

import os
import logging
from typing import Optional
from requre.storage import StorageCounter

logger = logging.getLogger(__name__)


class TempFile(StorageCounter):
    """
    replace system tempfile module with own predictable names implementation
     of temp files for mocking
    """

    root = "/tmp"
    prefix = "static_tmp"

    @classmethod
    def _get_name(cls, prefix: Optional[str] = None) -> str:
        cls.reset_counter_if_changed()
        filename = f"{prefix or cls.prefix}_{cls.next()}"
        os.makedirs(
            os.path.join(cls.root, cls.storage_file()), mode=0o777, exist_ok=True
        )
        output = os.path.join(cls.root, cls.storage_file(), filename)
        logger.debug(f"Use name for tempfile: ${output}")
        return output

    @classmethod
    def mktemp(cls, prefix: Optional[str] = None) -> str:
        return cls._get_name(prefix)

    @classmethod
    def mkdtemp(cls, prefix: Optional[str] = None) -> str:
        name = cls._get_name(prefix)
        os.makedirs(name)
        return name
