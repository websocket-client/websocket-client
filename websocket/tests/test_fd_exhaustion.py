# -*- coding: utf-8 -*-
#
import errno
import socket
import unittest
from unittest import mock

from websocket._http import (
    _is_fd_exhaustion,
    _open_socket,
    _with_fd_exhaustion_hint,
)

"""
test_fd_exhaustion.py
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

# Regression tests for
# https://github.com/websocket-client/websocket-client/issues/979
# ("Too many open files" when opening many connections at once).
# All file-descriptor exhaustion here is simulated with mocks; no test
# actually exhausts the process' file descriptors.


def _addrinfo_list():
    return [(socket.AF_INET, socket.SOCK_STREAM, 0, "", ("127.0.0.1", 80))]


class TestFdExhaustionHint(unittest.TestCase):
    def test_is_fd_exhaustion(self):
        self.assertTrue(_is_fd_exhaustion(OSError(errno.EMFILE, "Too many open files")))
        self.assertTrue(_is_fd_exhaustion(OSError(errno.ENFILE, "Too many open files in system")))
        self.assertFalse(_is_fd_exhaustion(OSError(errno.ECONNREFUSED, "Connection refused")))
        self.assertFalse(_is_fd_exhaustion(OSError(errno.EPIPE, "Broken pipe")))
        self.assertFalse(_is_fd_exhaustion(ValueError("not an OSError")))

    def test_hint_preserves_errno_and_chains_cause(self):
        original = OSError(errno.EMFILE, "Too many open files")
        hinted = _with_fd_exhaustion_hint(original)
        self.assertIsInstance(hinted, OSError)
        self.assertEqual(hinted.errno, errno.EMFILE)
        self.assertIn("Too many open files", str(hinted))
        self.assertIn("file descriptor", str(hinted))
        self.assertIn("ulimit -n", str(hinted))
        self.assertIsInstance(hinted.__cause__, OSError)

    def test_open_socket_creation_emfile_gets_hint(self):
        with mock.patch("websocket._http.socket.socket") as mock_socket:
            mock_socket.side_effect = OSError(errno.EMFILE, "Too many open files")
            with self.assertRaises(OSError) as ctx:
                _open_socket(_addrinfo_list(), [], timeout=5)
        self.assertEqual(ctx.exception.errno, errno.EMFILE)
        self.assertIn("file descriptor", str(ctx.exception))
        self.assertIn("ulimit -n", str(ctx.exception))
        self.assertIsInstance(ctx.exception.__cause__, OSError)

    def test_open_socket_creation_enfile_gets_hint(self):
        with mock.patch("websocket._http.socket.socket") as mock_socket:
            mock_socket.side_effect = OSError(errno.ENFILE, "Too many open files in system")
            with self.assertRaises(OSError) as ctx:
                _open_socket(_addrinfo_list(), [], timeout=5)
        self.assertEqual(ctx.exception.errno, errno.ENFILE)
        self.assertIn("file descriptor", str(ctx.exception))

    def test_open_socket_connect_emfile_gets_hint(self):
        mock_sock = mock.Mock()
        mock_sock.connect.side_effect = OSError(errno.EMFILE, "Too many open files")
        with mock.patch("websocket._http.socket.socket", return_value=mock_sock):
            with self.assertRaises(OSError) as ctx:
                _open_socket(_addrinfo_list(), [], timeout=5)
        self.assertEqual(ctx.exception.errno, errno.EMFILE)
        self.assertIn("ulimit -n", str(ctx.exception))
        mock_sock.close.assert_called()

    def test_open_socket_other_errors_unchanged(self):
        # ECONNREFUSED keeps the existing retry-then-reraise behaviour
        # and must NOT gain the file-descriptor hint.
        mock_sock = mock.Mock()
        mock_sock.connect.side_effect = OSError(errno.ECONNREFUSED, "Connection refused")
        with mock.patch("websocket._http.socket.socket", return_value=mock_sock):
            with self.assertRaises(OSError) as ctx:
                _open_socket(_addrinfo_list(), [], timeout=5)
        self.assertEqual(ctx.exception.errno, errno.ECONNREFUSED)
        self.assertNotIn("ulimit", str(ctx.exception))
        self.assertNotIn("file descriptor", str(ctx.exception))


if __name__ == "__main__":
    unittest.main()
