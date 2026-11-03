from typing import Any, Optional, Union

"""
_utils.py
websocket - WebSocket client library for Python

Copyright 2026 engn33r

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
"""
__all__ = ["NoLock", "validate_utf8", "extract_err_message", "extract_error_code"]


class NoLock:
    def __enter__(self) -> None:
        pass

    def __exit__(self, exc_type: Any, exc_value: Any, traceback: Any) -> None:
        pass


def _validate_utf8(utfbytes: bytes) -> bool:
    # Python's built-in UTF-8 decoder applies the same rules as a dedicated
    # validator and runs in C, so it is faster than a pure-Python loop or
    # wsaccel's validator.
    try:
        utfbytes.decode("utf-8")
    except UnicodeDecodeError as e:
        # Data that stops partway through a character has always been accepted.
        return e.reason == "unexpected end of data"
    return True


def validate_utf8(utfbytes: Union[str, bytes]) -> bool:
    """
    validate utf8 byte string.
    utfbytes: utf byte string to check.
    return value: if valid utf8 string, return true. Otherwise, return false.
    """
    if isinstance(utfbytes, str):
        utfbytes = utfbytes.encode("utf-8", "surrogatepass")
    return _validate_utf8(utfbytes)


def extract_err_message(exception: Exception) -> Optional[str]:
    if exception.args:
        return str(exception.args[0])
    else:
        return None


def extract_error_code(exception: Exception) -> Optional[int]:
    if exception.args and len(exception.args) > 1:
        return exception.args[0] if isinstance(exception.args[0], int) else None
    return None
