# -*- coding: utf-8 -*-
import sys
import unittest

"""
test_utils.py
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


class UtilsTest(unittest.TestCase):
    def test_nolock(self):
        """Test NoLock context manager"""
        from websocket._utils import NoLock

        lock = NoLock()

        # Test that it can be used as context manager
        with lock:
            pass  # Should not raise any exception

        # Test enter/exit methods directly
        self.assertIsNone(lock.__enter__())
        self.assertIsNone(lock.__exit__(None, None, None))

    def test_utf8_validation(self):
        """Test UTF-8 validation"""
        from websocket._utils import validate_utf8

        self.assertTrue(validate_utf8("Hello, World!".encode("utf-8")))
        self.assertTrue(validate_utf8("🌟 Unicode test".encode("utf-8")))
        self.assertTrue(validate_utf8(b"Hello, bytes"))
        self.assertTrue(validate_utf8("Héllo with accénts".encode("utf-8")))
        self.assertTrue(validate_utf8(b""))

        self.assertFalse(validate_utf8(b"\xff\xfe"))  # Invalid UTF-8
        self.assertFalse(validate_utf8(b"\x80\x80"))  # Invalid continuation

    def test_utf8_validation_edge_cases(self):
        """Test UTF-8 validation on boundary and invalid sequences"""
        from websocket._utils import validate_utf8

        valid = [
            b"\x00\x7f",
            b"\xc2\x80\xdf\xbf",  # first and last 2-byte characters
            b"\xe0\xa0\x80\xed\x9f\xbf\xee\x80\x80\xef\xbf\xbf",
            b"\xf0\x90\x80\x80\xf4\x8f\xbf\xbf",  # U+10000 and U+10FFFF
            "Grüße こんにちは 🌟".encode("utf-8") * 20000,
            # data that stops partway through a character is accepted
            b"\xc3",
            b"\xe2\x82",
            b"abc\xf0\x9f\x8c",
        ]
        invalid = [
            b"\x80",
            b"\xc0\x80",  # overlong
            b"\xc1\xbf",  # overlong
            b"\xe0\x80\x80",  # overlong
            b"\xed\xa0\x80",  # surrogate
            b"\xed\xa0",  # start of a surrogate
            b"\xf0\x80",  # start of an overlong
            b"\xf4\x90\x80\x80",  # above U+10FFFF
            b"\xf4\x90",  # start of a character above U+10FFFF
            b"\xf5",
            b"\xff",
            b"\xe2\x82A",
            b"\xe2\x82\xff",
            "Grüße こんにちは 🌟".encode("utf-8") * 20000 + b"\xff" + b"a" * 1000,
        ]
        for data in valid:
            self.assertTrue(validate_utf8(data), data[:20])
        for data in invalid:
            self.assertFalse(validate_utf8(data), data[:20])

    def test_extract_err_message(self):
        """Test extract_err_message function"""
        from websocket._utils import extract_err_message

        # Test with exception that has args
        exc_with_args = Exception("Test error message")
        self.assertEqual(extract_err_message(exc_with_args), "Test error message")

        # Test with exception that has multiple args
        exc_multi_args = Exception("First arg", "Second arg")
        self.assertEqual(extract_err_message(exc_multi_args), "First arg")

        # Test with exception that has no args
        exc_no_args = Exception()
        self.assertIsNone(extract_err_message(exc_no_args))

        # Test with exception whose first arg is not a str (e.g. OSError errno)
        self.assertEqual(extract_err_message(OSError(32, "Broken pipe")), "32")

    def test_extract_error_code(self):
        """Test extract_error_code function"""
        from websocket._utils import extract_error_code

        # Test with exception that has integer as first arg
        exc_with_code = Exception(404, "Not found")
        self.assertEqual(extract_error_code(exc_with_code), 404)

        # Test with exception that has string as first arg
        exc_with_string = Exception("Error message", "Second arg")
        self.assertIsNone(extract_error_code(exc_with_string))

        # Test with exception that has only one arg
        exc_single_arg = Exception("Single arg")
        self.assertIsNone(extract_error_code(exc_single_arg))

        # Test with exception that has no args
        exc_no_args = Exception()
        self.assertIsNone(extract_error_code(exc_no_args))

    def tearDown(self):
        """Clean up after tests"""
        # Ensure _utils is reimported fresh for next test
        if "websocket._utils" in sys.modules:
            del sys.modules["websocket._utils"]


if __name__ == "__main__":
    unittest.main()
