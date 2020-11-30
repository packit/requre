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
from urllib.parse import urlparse

from requests.models import Response, Request, PreparedRequest
from requests.structures import CaseInsensitiveDict

from requre.objects import ObjectStorage
from requre.cassette import Cassette


def remove_password_from_url(url):
    urlobject = urlparse(url)
    if urlobject.password:
        return urlobject._replace(
            netloc="{}:{}@{}".format(urlobject.username, "???", urlobject.hostname)
        ).geturl()
    else:
        return url


class RequestResponseHandling(ObjectStorage):
    __response_keys = ["status_code", "encoding", "reason"]
    __ignored = ["cookies"]
    __response_keys_special = ["raw", "_next", "headers", "elapsed", "_content"]
    __store_indicator = "__store_indicator"
    __implicit_encoding = "UTF-8"

    def __init__(
        self,
        store_keys: list,
        cassette: Optional[Cassette] = None,
        response_headers_to_drop=None,
    ) -> None:
        # replace request if given as key and use prettier url
        for index, key in enumerate(store_keys):
            if isinstance(key, (Request, PreparedRequest)):
                store_keys[index] = remove_password_from_url(key.url)
                store_keys.insert(index, key.method)
        super().__init__(store_keys, cassette=cassette)
        self.response_headers_to_drop = response_headers_to_drop or []

    def write(self, response: Response, metadata: Optional[Dict] = None) -> Response:
        super().write(response, metadata)
        # TODO: disabled for now, improve next handling if we find it makes sense
        # if getattr(response, "next"):
        #    self.write(getattr(response, "next"))
        return response

    def read(self):
        data = super().read()
        # TODO: disabled for now, improve next handling if we find it makes sense
        # if getattr(data, "next"):
        #    data._next = self.read()
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
                headers_dict = dict(response.headers)
                for header in self.response_headers_to_drop:
                    if header in headers_dict:
                        headers_dict[header] = None
                output[key] = headers_dict
            if key == "elapsed":
                output[key] = response.elapsed.total_seconds()
            if key == "_content":
                what_store = response._content  # type: ignore
                encoding = response.encoding or self.__implicit_encoding
                try:
                    what_store = what_store.decode(encoding)  # type: ignore
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

    @classmethod
    def decorator_all_keys(
        cls,
        storage_object_kwargs=None,
        cassette: Cassette = None,
        response_headers_to_drop=None,
    ) -> Any:
        """
        Class method for what should be used as decorator of import replacing system
        This use all arguments of function as keys

        :param func: Callable object
        :param storage_object_kwargs: forwarded to the storage object
        :param response_headers_to_drop: list of header names we don't want to save with response
                                            (Will be replaced to `None`.)
        :param cassette: Cassette instance to pass inside object to work with
        :return: CassetteExecution class with function and cassette instance
        """
        storage_object_kwargs = storage_object_kwargs or {}
        if response_headers_to_drop:
            storage_object_kwargs["response_headers_to_drop"] = response_headers_to_drop
        return super().decorator_all_keys(storage_object_kwargs, cassette=cassette)

    @classmethod
    def decorator(
        cls,
        *,
        item_list: list,
        map_function_to_item=None,
        storage_object_kwargs=None,
        cassette: Cassette = None,
        response_headers_to_drop=None
    ) -> Any:
        """
        Class method for what should be used as decorator of import replacing system
        This use list of selection of *args or **kwargs as arguments of function as keys

        :param item_list: list of values of *args nums,  **kwargs names to use as keys
        :param map_function_to_item: dict of function to apply to keys before storing
                                  (have to be listed in item_list)
        :param storage_object_kwargs: forwarded to the storage object
        :param response_headers_to_drop: list of header names we don't want to save with response
                                        (Will be replaced to `None`.)
        :param cassette: Cassette instance to pass inside object to work with
        :return: CassetteExecution class with function and cassette instance
        """
        storage_object_kwargs = storage_object_kwargs or {}
        if response_headers_to_drop:
            storage_object_kwargs["response_headers_to_drop"] = response_headers_to_drop
        return super().decorator(
            item_list=item_list,
            map_function_to_item=map_function_to_item,
            storage_object_kwargs=storage_object_kwargs,
            cassette=cassette,
        )

    @classmethod
    def decorator_plain(
        cls,
        storage_object_kwargs=None,
        cassette: Cassette = None,
        response_headers_to_drop=None,
    ) -> Any:
        """
        Class method for what should be used as decorator of import replacing system
        This use no arguments of function as keys

        :param func: Callable object
        :param storage_object_kwargs: forwarded to the storage object
        :param response_headers_to_drop: list of header names we don't want to save with response
                                          (Will be replaced to `None`.)
        :param cassette: Cassette instance to pass inside object to work with
        :return: CassetteExecution class with function and cassette instance
        """
        storage_object_kwargs = storage_object_kwargs or {}
        if response_headers_to_drop:
            storage_object_kwargs["response_headers_to_drop"] = response_headers_to_drop
        return super().decorator_plain(
            storage_object_kwargs=storage_object_kwargs, cassette=cassette
        )
