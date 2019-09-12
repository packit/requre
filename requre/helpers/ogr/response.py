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


from typing import Optional
from requre.storage import PersistentObjectStorage


class RequestResponse:
    def __init__(
        self,
        status_code: int,
        ok: bool,
        content: bytes,
        json: Optional[dict] = None,
        reason=None,
        headers: Optional[list] = None,
        links: Optional[list] = None,
        exception: Optional[dict] = None,
    ) -> None:
        self.status_code = status_code
        self.ok = ok
        self.content = content
        self.json_content = json
        self.reason = reason
        self.headers = dict(headers) if headers else None
        self.links = links
        self.exception = exception

    def __str__(self) -> str:
        return (
            f"RequestResponse("
            f"status_code={self.status_code}, "
            f"ok={self.ok}, "
            f"content={self.content}, "
            f"json={self.json_content}, "
            f"reason={self.reason}, "
            f"headers={self.headers}, "
            f"links={self.links}, "
            f"exception={self.exception})"
        )

    def __eq__(self, o: object) -> bool:
        if not isinstance(o, RequestResponse):
            return False
        return (
            self.status_code == o.status_code
            and self.ok == o.ok
            and self.content == o.content
            and self.json_content == o.json_content
            and self.reason == o.reason
            and self.headers == o.headers
            and self.links == o.links
            and self.exception == o.exception
        )

    def to_json_format(self) -> dict:
        return {
            "status_code": self.status_code,
            "ok": self.ok,
            "content": self.content,
            "json": self.json_content,
            "reason": self.reason,
            "headers": self.headers,
            "links": self.links,
            "exception": self.exception,
        }

    def json(self):
        return self.json_content


def use_persistent_storage(cls):
    class ClassWithPersistentStorage(cls):
        persistent_storage: Optional[
            PersistentObjectStorage
        ] = PersistentObjectStorage()

        def get_raw_request(
            self, url, method="GET", params=None, data=None, header=None
        ):
            keys_internal = [method, url, params, data]
            if self.persistent_storage.is_write_mode:
                output = super().get_raw_request(
                    url, method=method, params=params, data=data, header=header
                )
                self.persistent_storage.store(
                    keys=keys_internal, values=output.to_json_format()
                )
            else:
                output_dict = self.persistent_storage.read(keys=keys_internal)
                output = RequestResponse(**output_dict)
            return output

    ClassWithPersistentStorage.__name__ = cls.__name__
    return ClassWithPersistentStorage
