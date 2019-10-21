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


import datetime
import json
from io import BytesIO
from typing import Any, Optional, Dict

from requests.models import Response
from requests.structures import CaseInsensitiveDict

from requre.objects import ObjectStorage


class RequestResponseHandling(ObjectStorage):
    __response_keys = ["status_code", "encoding", "reason"]
    __ignored = ["cookies"]
    __response_keys_special = ["raw", "_next", "headers", "elapsed", "_content"]
    __store_indicator = "__store_indicator"
    __implicit_encoding = "UTF-8"

    def write(self, response: Response, metadata: Optional[Dict] = None) -> Response:
        super().write(response, metadata)
        if getattr(response, "next"):
            self.write(getattr(response, "next"))
        return response

    def read(self):
        data = super().read()
        if getattr(data, "next"):
            data._next = self.read()
        return data

    def to_serializable(self, response: Response) -> Any:
        output = dict()
        for key in self.__response_keys:
            output[key] = getattr(response, key)
        for key in self.__response_keys_special:
            if key == "raw":
                binary_data = response.raw.read()
                output[key] = binary_data
                # replay it back to raw
                response.raw = BytesIO(binary_data)
            if key == "headers":
                output[key] = dict(response.headers)
            if key == "elapsed":
                output[key] = response.elapsed.total_seconds()
            if key == "_content":
                what_store = response._content  # type: ignore
                encoding = response.encoding or self.__implicit_encoding
                try:
                    what_store = what_store.decode(encoding)
                    try:
                        what_store = json.loads(what_store)
                        indicator = 2
                    except json.decoder.JSONDecodeError:
                        indicator = 1
                except (ValueError, AttributeError):
                    indicator = 0
                output[key] = what_store
                output[self.__store_indicator] = indicator
            if key == "_next":
                output[key] = None
                if getattr(response, "next") is not None:
                    output[key] = self.store_keys
        return output

    def from_serializable(self, data: Any) -> Response:
        response = Response()
        for key in self.__response_keys:
            setattr(response, key, data[key])
        for key in self.__response_keys_special:
            if key == "raw":
                response.raw = BytesIO(data[key])
            if key == "headers":
                response.headers = CaseInsensitiveDict(data[key])
            if key == "elapsed":
                response.elapsed = datetime.timedelta(seconds=data[key])
            if key == "_content":
                encoding = response.encoding or self.__implicit_encoding
                indicator = data[self.__store_indicator]
                if indicator == 0:
                    what_store = data[key]
                elif indicator == 1:
                    what_store = data[key].encode(encoding)
                elif indicator == 2:
                    what_store = json.dumps(data[key])
                    what_store = what_store.encode(encoding)
                response._content = what_store  # type: ignore
            if key == "_next":
                setattr(response, "_next", data[key])
        return response
