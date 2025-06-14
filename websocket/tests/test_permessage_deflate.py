import os
import unittest

import websocket as ws
from websocket import WebSocket
from websocket._permessage_deflate import CompressionOptions

"""
test_permessage_deflate.py
websocket - WebSocket client library for Python

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.

--- 

This code is based on work of the python websockets library
https://github.com/python-websockets/websockets

Copyright Aymeric Augustin and contributors

Licensed under the following BSD-3-Clause License:

Redistribution and use in source and binary forms, with or without
modification, are permitted provided that the following conditions are met:

    * Redistributions of source code must retain the above copyright notice,
      this list of conditions and the following disclaimer.
    * Redistributions in binary form must reproduce the above copyright notice,
      this list of conditions and the following disclaimer in the documentation
      and/or other materials provided with the distribution.
    * Neither the name of the copyright holder nor the names of its contributors
      may be used to endorse or promote products derived from this software
      without specific prior written permission.

THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND
ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE
FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL
DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR
SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER
CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY,
OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
"""

# Skip test to access the internet unless TEST_WITH_INTERNET == 1
TEST_WITH_INTERNET = os.environ.get("TEST_WITH_INTERNET", "0") == "1"
# Skip tests relying on local websockets server unless LOCAL_WS_SERVER_PORT != -1
LOCAL_WS_SERVER_PORT = os.environ.get("LOCAL_WS_SERVER_PORT", "-1")
TEST_WITH_LOCAL_SERVER = LOCAL_WS_SERVER_PORT != "-1"
TRACEABLE = True


class CompressionOptionsParserTest(unittest.TestCase):
    def test_serialize_to_header(self):
        options = CompressionOptions(False, False, 10, 11)
        self.assertEqual("permessage-deflate; server_max_window_bits=10; client_max_window_bits=11",
                         options.to_header())

        options = CompressionOptions(client_max_window_bits=True)
        self.assertEqual("permessage-deflate; client_max_window_bits", options.to_header())

        options = CompressionOptions(True, True, client_max_window_bits=None)
        self.assertEqual("permessage-deflate; server_no_context_takeover; client_no_context_takeover",
                         options.to_header())

    def test_deserialize_from_header(self):
        options = CompressionOptions.from_header(
            "permessage-deflate; server_max_window_bits=10; client_max_window_bits=11")
        self.assertEqual(10, options.server_max_window_bits)
        self.assertEqual(11, options.client_max_window_bits)
        self.assertFalse(options.server_no_context_takeover)
        self.assertFalse(options.client_no_context_takeover)

        options = CompressionOptions.from_header("permessage-deflate; client_max_window_bits;")
        self.assertIsNone(options.server_max_window_bits)
        self.assertTrue(options.client_max_window_bits)
        self.assertFalse(options.server_no_context_takeover)
        self.assertFalse(options.client_no_context_takeover)

        options = CompressionOptions.from_header(
            "permessage-deflate; server_no_context_takeover;   client_no_context_takeover")
        self.assertIsNone(options.server_max_window_bits)
        self.assertIsNone(options.client_max_window_bits)
        self.assertTrue(options.server_no_context_takeover)
        self.assertTrue(options.client_no_context_takeover)

    def test_negotiation_server_no_context_takeover(self):
        no_context_true = CompressionOptions(server_no_context_takeover=True)
        no_context_false = CompressionOptions(server_no_context_takeover=False)

        # Client: False, Server: False -> False
        result = no_context_false.negotiate(no_context_false)
        self.assertFalse(result.server_no_context_takeover)

        # Client: False, Server: True -> True
        result = no_context_false.negotiate(no_context_true)
        self.assertTrue(result.server_no_context_takeover)

        # Client: True, Server: False -> ValueError
        with self.assertRaises(ValueError):
            no_context_true.negotiate(no_context_false)

        # Client: True, Server: True -> True
        result = no_context_true.negotiate(no_context_true)
        self.assertTrue(result.server_no_context_takeover)

    def test_negotiation_client_no_context_takeover(self):
        no_context_true = CompressionOptions(client_no_context_takeover=True)
        no_context_false = CompressionOptions(client_no_context_takeover=False)

        # Client: False, Server: False -> False
        result = no_context_false.negotiate(no_context_false)
        self.assertFalse(result.client_no_context_takeover)

        # Client: False, Server: True -> True
        result = no_context_false.negotiate(no_context_true)
        self.assertTrue(result.client_no_context_takeover)

        # Client: True, Server: False -> True
        result = no_context_true.negotiate(no_context_false)
        self.assertTrue(result.client_no_context_takeover)

        # Client: True, Server: True -> True
        result = no_context_true.negotiate(no_context_true)
        self.assertTrue(result.client_no_context_takeover)

    def test_negotiation_server_max_window_bits(self):
        options_none = CompressionOptions(server_max_window_bits=None)
        options_10 = CompressionOptions(server_max_window_bits=10)
        options_12 = CompressionOptions(server_max_window_bits=12)

        # Client: None, Server: None -> default: max
        result = options_none.negotiate(options_none)
        self.assertEqual(15, result.server_max_window_bits)

        # Client: None, Server: 10 -> 10
        result = options_none.negotiate(options_10)
        self.assertEqual(10, result.server_max_window_bits)

        # Client: 10, Server: None -> ValueError
        with self.assertRaises(ValueError):
            options_10.negotiate(options_none)

        # Client 12: Server: 10 -> 10
        result = options_12.negotiate(options_10)
        self.assertEqual(10, result.server_max_window_bits)

        # Client: 10, Server: 12 -> ValueError
        with self.assertRaises(ValueError):
            options_10.negotiate(options_12)

    def test_negotiation_client_max_window_bits(self):
        options_none = CompressionOptions(client_max_window_bits=None)
        options_true = CompressionOptions(client_max_window_bits=True)
        options_10 = CompressionOptions(client_max_window_bits=10)
        options_12 = CompressionOptions(client_max_window_bits=12)

        # Client: None, Server: None -> default: max
        result = options_none.negotiate(options_none)
        self.assertEqual(15, result.client_max_window_bits)

        # Client: None, Server: 10 -> ValueError
        with self.assertRaises(ValueError):
            options_none.negotiate(options_10)

        # Client: True, Server: None -> default: max
        result = options_true.negotiate(options_none)
        self.assertEqual(15, result.client_max_window_bits)

        # Client: True, Server: 10 -> 10
        result = options_true.negotiate(options_10)
        self.assertEqual(10, result.client_max_window_bits)

        # Client: 10, Server: None -> 10
        result = options_10.negotiate(options_none)
        self.assertEqual(10, result.client_max_window_bits)

        # Client: 12, Server: 10 -> 10
        result = options_12.negotiate(options_10)
        self.assertEqual(10, result.client_max_window_bits)

        # Client: 10, Server: 12 -> ValueError
        with self.assertRaises(ValueError):
            options_10.negotiate(options_12)


class CompressionEndToEndTests(unittest.TestCase):
    @unittest.skipUnless(
        TEST_WITH_LOCAL_SERVER, "Tests using local websocket server are disabled"
    )
    def test_compression_context_takeover(self):
        """
        tests that compressor/decompressor's are correctly reset depending on the negotiated parameters
        or during re-connects
        """
        url = f"ws://127.0.0.1:{LOCAL_WS_SERVER_PORT}"
        s: WebSocket = ws.create_connection(url, compression=True)

        def _generate_traffic():
            for x in range(10):
                s.send("Hello, World")
                result = s.recv()
                self.assertEqual(result, "Hello, World")

        # ensure the compressor/decompressor were re-used and not reset
        c, d = s.compression_extension.compressor, s.compression_extension.decompressor
        _generate_traffic()
        self.assertIs(c, s.compression_extension.compressor)
        self.assertIs(d, s.compression_extension.decompressor)

        # reconnect without server context takeover
        s.close()
        s.connect(url, compression=CompressionOptions(server_no_context_takeover=True))

        # ensure the re-connecting also resets the compressor, otherwise the states would differ on client/server
        self.assertIsNot(c, s.compression_extension.compressor)

        # ensure the compressor/decompressor were re-used and not reset
        c, d = s.compression_extension.compressor, s.compression_extension.decompressor
        _generate_traffic()
        self.assertIs(c, s.compression_extension.compressor)
        self.assertIsNot(d, s.compression_extension.decompressor)

        # reconnect without client context takeover
        s.close()
        s.connect(url, compression=CompressionOptions(server_no_context_takeover=True))

        c, d = s.compression_extension.compressor, s.compression_extension.decompressor
        _generate_traffic()
        self.assertIs(c, s.compression_extension.compressor)
        self.assertIsNot(d, s.compression_extension.decompressor)
