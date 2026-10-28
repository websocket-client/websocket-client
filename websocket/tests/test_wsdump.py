import unittest
from unittest import mock

import websocket
from websocket import _wsdump

"""
test_wsdump.py
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

# OSC title, clear screen, OSC 52 clipboard query: what a hostile server sends
EVIL = "\x1b]0;pwned\x07\x1b[2J\x1b]52;c;?\x07"


class WsdumpEscapingTest(unittest.TestCase):
    def test_escape_control_chars_keeps_newlines(self):
        self.assertEqual(
            _wsdump.escape_control_chars(f"a{EVIL}\tb\nc\r\x9b"),
            "a\\x1b]0;pwned\\x07\\x1b[2J\\x1b]52;c;?\\x07\tb\nc\\x0d\\x9b",
        )

    def test_console_script_escapes_server_text_in_errors(self):
        """The installed wsdump command calls main() directly (N165): an error
        still ends with a traceback and exit status 1, but the server's text
        in it is escaped."""
        error = websocket.WebSocketException(f"Handshake status 500 Oops{EVIL}")
        with mock.patch("sys.argv", ["wsdump", "ws://example.com/"]), mock.patch(
            "websocket.create_connection", side_effect=error
        ), self.assertRaises(SystemExit) as cm:
            _wsdump.main()
        message = cm.exception.code
        assert isinstance(message, str), message  # printed to stderr, exit status 1
        self.assertIn("Traceback (most recent call last)", message)
        self.assertIn("Oops\\x1b]0;pwned\\x07\\x1b[2J", message)
        self.assertNotIn("\x1b", message)


if __name__ == "__main__":
    unittest.main()
