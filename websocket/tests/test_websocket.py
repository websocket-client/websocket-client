# -*- coding: utf-8 -*-
#
import io
import logging
import os
import os.path
import socket
import struct
import threading
import time
import unittest
from base64 import decodebytes as base64decode
from base64 import encodebytes as base64encode
from unittest import mock

import websocket as ws
from websocket._abnf import ABNF
from websocket._cookiejar import SimpleCookieJar
from websocket.tests._fakes import HeaderSockMock, SockMock
from websocket._exceptions import (
    WebSocketBadStatusException,
    WebSocketAddressException,
    WebSocketException,
)
from websocket._handshake import CookieJar
from websocket._handshake import _create_sec_websocket_key
from websocket._handshake import _validate as _validate_header
from websocket._handshake import _get_handshake_headers
from websocket._handshake import handshake_response
from websocket._http import _tunnel, read_headers
from websocket._utils import validate_utf8

"""
test_websocket.py
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

try:
    import ssl
except ImportError:
    # dummy class of SSLError for ssl none-support environment.
    class SSLError(Exception):
        pass


# Skip test to access the internet unless TEST_WITH_INTERNET == 1
TEST_WITH_INTERNET = os.environ.get("TEST_WITH_INTERNET", "0") == "1"
# Skip tests relying on local websockets server unless LOCAL_WS_SERVER_PORT != -1
LOCAL_WS_SERVER_PORT = os.environ.get("LOCAL_WS_SERVER_PORT", "-1")
TEST_WITH_LOCAL_SERVER = LOCAL_WS_SERVER_PORT != "-1"
TRACEABLE = True


def create_mask_key(_):
    return "abcd"


class WebSocketTest(unittest.TestCase):
    def setUp(self):
        ws.enableTrace(TRACEABLE)

    def tearDown(self):
        pass

    def test_default_timeout(self):
        self.assertEqual(ws.getdefaulttimeout(), None)
        ws.setdefaulttimeout(10)
        self.assertEqual(ws.getdefaulttimeout(), 10)
        ws.setdefaulttimeout(None)

    def test_default_timeout_rejects_bool_and_nonfinite(self):
        """bool subclasses int; True must not become a 1s default timeout."""
        for value in (True, False):
            with self.assertRaises(TypeError):
                ws.setdefaulttimeout(value)
        for value in (float("nan"), float("inf"), float("-inf")):
            with self.assertRaises(ValueError):
                ws.setdefaulttimeout(value)
        ws.setdefaulttimeout(None)

    def test_ws_key(self):
        key = _create_sec_websocket_key()
        self.assertTrue(key != 24)
        self.assertTrue("¥n" not in key)

    def test_nonce(self):
        """WebSocket key should be a random 16-byte nonce."""
        key = _create_sec_websocket_key()
        nonce = base64decode(key.encode("utf-8"))
        self.assertEqual(16, len(nonce))

    def test_ws_utils(self):
        key = "c6b8hTg4EeGb2gQMztV1/g=="
        required_header = {
            "upgrade": "websocket",
            "connection": "upgrade",
            "sec-websocket-accept": "Kxep+hNu9n51529fGidYu7a3wO0=",
        }
        self.assertEqual(_validate_header(required_header, key, None), (True, None))

        header = required_header.copy()
        header["upgrade"] = "http"
        self.assertEqual(_validate_header(header, key, None), (False, None))
        del header["upgrade"]
        self.assertEqual(_validate_header(header, key, None), (False, None))

        header = required_header.copy()
        header["connection"] = "something"
        self.assertEqual(_validate_header(header, key, None), (False, None))
        del header["connection"]
        self.assertEqual(_validate_header(header, key, None), (False, None))

        header = required_header.copy()
        header["sec-websocket-accept"] = "something"
        self.assertEqual(_validate_header(header, key, None), (False, None))
        del header["sec-websocket-accept"]
        self.assertEqual(_validate_header(header, key, None), (False, None))

        header = required_header.copy()
        header["sec-websocket-protocol"] = "sub1"
        self.assertEqual(
            _validate_header(header, key, ["sub1", "sub2"]), (True, "sub1")
        )
        # This case will print out a logging error using the error() function, but that is expected
        self.assertEqual(_validate_header(header, key, ["sub2", "sub3"]), (False, None))

        header = required_header.copy()
        header["sec-websocket-protocol"] = "sUb1"
        self.assertEqual(
            _validate_header(header, key, ["Sub1", "suB2"]), (True, "sub1")
        )

        header = required_header.copy()
        # This case will print out a logging error using the error() function, but that is expected
        self.assertEqual(_validate_header(header, key, ["Sub1", "suB2"]), (False, None))

    def test_read_header(self):
        status, header, _ = read_headers(HeaderSockMock("data/header01.txt"))
        self.assertEqual(status, 101)
        self.assertEqual(header["connection"], "Upgrade")

        status, header, _ = read_headers(HeaderSockMock("data/header03.txt"))
        self.assertEqual(status, 101)
        self.assertEqual(header["connection"], "Upgrade, Keep-Alive")

        HeaderSockMock("data/header02.txt")
        self.assertRaises(
            ws.WebSocketException, read_headers, HeaderSockMock("data/header02.txt")
        )

    def test_send(self):
        # TODO: add longer frame data
        sock = ws.WebSocket()
        sock.set_mask_key(create_mask_key)
        s = sock.sock = HeaderSockMock("data/header01.txt")
        sock.send("Hello")
        self.assertEqual(s.sent[0], b"\x81\x85abcd)\x07\x0f\x08\x0e")

        sock.send("こんにちは")
        self.assertEqual(
            s.sent[1],
            b"\x81\x8fabcd\x82\xe3\xf0\x87\xe3\xf1\x80\xe5\xca\x81\xe2\xc5\x82\xe3\xcc",
        )

        #        sock.send("x" * 5000)
        #        self.assertEqual(s.sent[1], b'\x81\x8fabcd\x82\xe3\xf0\x87\xe3\xf1\x80\xe5\xca\x81\xe2\xc5\x82\xe3\xcc")

        self.assertEqual(sock.send_binary(b"1111111111101"), 19)

    def test_send_close_accepts_text_reason(self):
        sock = ws.WebSocket()
        captured = {}

        def fake_send(payload, opcode):
            captured["payload"] = payload
            captured["opcode"] = opcode
            return len(payload)

        sock.send = fake_send  # type: ignore[assignment]
        sock.connected = True

        sock.send_close(reason="normal close")

        self.assertEqual(captured["opcode"], ws.ABNF.OPCODE_CLOSE)
        self.assertIsInstance(captured["payload"], (bytes, bytearray))
        self.assertTrue(captured["payload"].endswith(b"normal close"))

    def test_close_accepts_text_reason(self):
        sock = ws.WebSocket()
        captured = {}

        def fake_send(payload, opcode):
            captured["payload"] = payload
            captured["opcode"] = opcode
            return len(payload)

        sock.send = fake_send  # type: ignore[assignment]
        sock.connected = True

        sock.close(reason="normal close")

        self.assertEqual(captured["opcode"], ws.ABNF.OPCODE_CLOSE)
        self.assertIsInstance(captured["payload"], (bytes, bytearray))
        self.assertTrue(captured["payload"].endswith(b"normal close"))

    def test_recv(self):
        # TODO: add longer frame data
        sock = ws.WebSocket()
        s = sock.sock = SockMock()
        something = (
            b"\x81\x8fabcd\x82\xe3\xf0\x87\xe3\xf1\x80\xe5\xca\x81\xe2\xc5\x82\xe3\xcc"
        )
        s.add_packet(something)
        data = sock.recv()
        self.assertEqual(data, "こんにちは")

        s.add_packet(b"\x81\x85abcd)\x07\x0f\x08\x0e")
        data = sock.recv()
        self.assertEqual(data, "Hello")

    @unittest.skipUnless(TEST_WITH_INTERNET, "Internet-requiring tests are disabled")
    def test_iter(self):
        count = 2
        s = ws.create_connection("wss://api.bitfinex.com/ws/2")
        try:
            s.send('{"event": "subscribe", "channel": "ticker"}')
            for _ in s:
                count -= 1
                if count == 0:
                    break
            self.assertEqual(
                count, 0, "WebSocket iterator failed to yield the expected frames"
            )
        finally:
            s.close()

    @unittest.skipUnless(TEST_WITH_INTERNET, "Internet-requiring tests are disabled")
    def test_next(self):
        sock = ws.create_connection("wss://api.bitfinex.com/ws/2")
        try:
            self.assertEqual(str, type(next(sock)))
        finally:
            sock.close()

    def test_internal_recv_strict(self):
        sock = ws.WebSocket()
        s = sock.sock = SockMock()
        s.add_packet(b"foo")
        s.add_packet(socket.timeout())
        s.add_packet(b"bar")
        # s.add_packet(SSLError("The read operation timed out"))
        s.add_packet(b"baz")
        with self.assertRaises(ws.WebSocketTimeoutException):
            sock.frame_buffer.recv_strict(9)
        #     with self.assertRaises(SSLError):
        #         data = sock._recv_strict(9)
        data = sock.frame_buffer.recv_strict(9)
        self.assertEqual(data, b"foobarbaz")
        with self.assertRaises(ws.WebSocketConnectionClosedException):
            sock.frame_buffer.recv_strict(1)

    def test_recv_timeout(self):
        sock = ws.WebSocket()
        s = sock.sock = SockMock()
        s.add_packet(b"\x81")
        s.add_packet(socket.timeout())
        s.add_packet(b"\x8dabcd\x29\x07\x0f\x08\x0e")
        s.add_packet(socket.timeout())
        s.add_packet(b"\x4e\x43\x33\x0e\x10\x0f\x00\x40")
        with self.assertRaises(ws.WebSocketTimeoutException):
            sock.recv()
        with self.assertRaises(ws.WebSocketTimeoutException):
            sock.recv()
        data = sock.recv()
        self.assertEqual(data, "Hello, World!")
        with self.assertRaises(ws.WebSocketConnectionClosedException):
            sock.recv()

    def test_recv_with_simple_fragmentation(self):
        sock = ws.WebSocket()
        s = sock.sock = SockMock()
        # OPCODE=TEXT, FIN=0, MSG="Brevity is "
        s.add_packet(b"\x01\x8babcd#\x10\x06\x12\x08\x16\x1aD\x08\x11C")
        # OPCODE=CONT, FIN=1, MSG="the soul of wit"
        s.add_packet(b"\x80\x8fabcd\x15\n\x06D\x12\r\x16\x08A\r\x05D\x16\x0b\x17")
        data = sock.recv()
        self.assertEqual(data, "Brevity is the soul of wit")
        with self.assertRaises(ws.WebSocketConnectionClosedException):
            sock.recv()

    def test_recv_with_fire_event_of_fragmentation(self):
        sock = ws.WebSocket(fire_cont_frame=True)
        s = sock.sock = SockMock()
        # OPCODE=TEXT, FIN=0, MSG="Brevity is "
        s.add_packet(b"\x01\x8babcd#\x10\x06\x12\x08\x16\x1aD\x08\x11C")
        # OPCODE=CONT, FIN=0, MSG="Brevity is "
        s.add_packet(b"\x00\x8babcd#\x10\x06\x12\x08\x16\x1aD\x08\x11C")
        # OPCODE=CONT, FIN=1, MSG="the soul of wit"
        s.add_packet(b"\x80\x8fabcd\x15\n\x06D\x12\r\x16\x08A\r\x05D\x16\x0b\x17")

        _, data = sock.recv_data()
        self.assertEqual(data, b"Brevity is ")
        _, data = sock.recv_data()
        self.assertEqual(data, b"Brevity is ")
        _, data = sock.recv_data()
        self.assertEqual(data, b"the soul of wit")

        # OPCODE=CONT, FIN=0, MSG="Brevity is "
        s.add_packet(b"\x80\x8babcd#\x10\x06\x12\x08\x16\x1aD\x08\x11C")

        with self.assertRaises(ws.WebSocketException):
            sock.recv_data()

        with self.assertRaises(ws.WebSocketConnectionClosedException):
            sock.recv()

    def test_close(self):
        sock = ws.WebSocket()
        sock.connected = True
        sock.close()

        sock = ws.WebSocket()
        s = sock.sock = SockMock()
        sock.connected = True
        s.add_packet(b"\x88\x80\x17\x98p\x84")
        sock.recv()
        self.assertEqual(sock.connected, False)

    def test_recv_cont_fragmentation(self):
        sock = ws.WebSocket()
        s = sock.sock = SockMock()
        # OPCODE=CONT, FIN=1, MSG="the soul of wit"
        s.add_packet(b"\x80\x8fabcd\x15\n\x06D\x12\r\x16\x08A\r\x05D\x16\x0b\x17")
        self.assertRaises(ws.WebSocketException, sock.recv)

    def test_recv_with_prolonged_fragmentation(self):
        sock = ws.WebSocket()
        s = sock.sock = SockMock()
        # OPCODE=TEXT, FIN=0, MSG="Once more unto the breach, "
        s.add_packet(
            b"\x01\x9babcd.\x0c\x00\x01A\x0f\x0c\x16\x04B\x16\n\x15\rC\x10\t\x07C\x06\x13\x07\x02\x07\tNC"
        )
        # OPCODE=CONT, FIN=0, MSG="dear friends, "
        s.add_packet(b"\x00\x8eabcd\x05\x07\x02\x16A\x04\x11\r\x04\x0c\x07\x17MB")
        # OPCODE=CONT, FIN=1, MSG="once more"
        s.add_packet(b"\x80\x89abcd\x0e\x0c\x00\x01A\x0f\x0c\x16\x04")
        data = sock.recv()
        self.assertEqual(data, "Once more unto the breach, dear friends, once more")
        with self.assertRaises(ws.WebSocketConnectionClosedException):
            sock.recv()

    def test_recv_with_fragmentation_and_control_frame(self):
        sock = ws.WebSocket()
        sock.set_mask_key(create_mask_key)
        s = sock.sock = SockMock()
        # OPCODE=TEXT, FIN=0, MSG="Too much "
        s.add_packet(b"\x01\x89abcd5\r\x0cD\x0c\x17\x00\x0cA")
        # OPCODE=PING, FIN=1, MSG="Please PONG this"
        s.add_packet(b"\x89\x90abcd1\x0e\x06\x05\x12\x07C4.,$D\x15\n\n\x17")
        # OPCODE=CONT, FIN=1, MSG="of a good thing"
        s.add_packet(b"\x80\x8fabcd\x0e\x04C\x05A\x05\x0c\x0b\x05B\x17\x0c\x08\x0c\x04")
        data = sock.recv()
        self.assertEqual(data, "Too much of a good thing")
        with self.assertRaises(ws.WebSocketConnectionClosedException):
            sock.recv()
        self.assertEqual(
            s.sent[0], b"\x8a\x90abcd1\x0e\x06\x05\x12\x07C4.,$D\x15\n\n\x17"
        )

    @unittest.skipUnless(
        TEST_WITH_LOCAL_SERVER, "Tests using local websocket server are disabled"
    )
    def test_websocket(self):
        s = ws.create_connection(f"ws://127.0.0.1:{LOCAL_WS_SERVER_PORT}")
        self.assertNotEqual(s, None)
        s.send("Hello, World")
        result = s.next()
        s.fileno()
        self.assertEqual(result, "Hello, World")

        s.send("こにゃにゃちは、世界")
        result = s.recv()
        self.assertEqual(result, "こにゃにゃちは、世界")
        self.assertRaises(ValueError, s.send_close, -1, "")
        s.close()

    @unittest.skipUnless(
        TEST_WITH_LOCAL_SERVER, "Tests using local websocket server are disabled"
    )
    def test_ping_pong(self):
        s = ws.create_connection(f"ws://127.0.0.1:{LOCAL_WS_SERVER_PORT}")
        self.assertNotEqual(s, None)
        s.ping("Hello")
        s.pong("Hi")
        s.close()

    @unittest.skipUnless(TEST_WITH_INTERNET, "Internet-requiring tests are disabled")
    def test_support_redirect(self):
        s = ws.WebSocket()
        self.assertRaises(WebSocketBadStatusException, s.connect, "ws://google.com/")
        # Need to find a URL that has a redirect code leading to a websocket

    @unittest.skipUnless(TEST_WITH_INTERNET, "Internet-requiring tests are disabled")
    def test_secure_websocket(self):
        s = ws.create_connection("wss://api.bitfinex.com/ws/2")
        self.assertNotEqual(s, None)
        self.assertTrue(isinstance(s.sock, ssl.SSLSocket))
        self.assertEqual(s.getstatus(), 101)
        self.assertNotEqual(s.getheaders(), None)
        s.settimeout(10)
        self.assertEqual(s.gettimeout(), 10)
        self.assertEqual(s.getsubprotocol(), None)
        s.abort()

    @unittest.skipUnless(
        TEST_WITH_LOCAL_SERVER, "Tests using local websocket server are disabled"
    )
    def test_websocket_with_custom_header(self):
        s = ws.create_connection(
            f"ws://127.0.0.1:{LOCAL_WS_SERVER_PORT}",
            header={"User-Agent": "PythonWebsocketClient"},
        )
        self.assertNotEqual(s, None)
        self.assertEqual(s.getsubprotocol(), None)
        s.send("Hello, World")
        result = s.recv()
        self.assertEqual(result, "Hello, World")
        self.assertRaises(ValueError, s.close, -1, "")
        s.close()

    @unittest.skipUnless(
        TEST_WITH_LOCAL_SERVER, "Tests using local websocket server are disabled"
    )
    def test_after_close(self):
        s = ws.create_connection(f"ws://127.0.0.1:{LOCAL_WS_SERVER_PORT}")
        self.assertNotEqual(s, None)
        s.close()
        self.assertRaises(ws.WebSocketConnectionClosedException, s.send, "Hello")
        self.assertRaises(ws.WebSocketConnectionClosedException, s.recv)


class SockOptTest(unittest.TestCase):
    @unittest.skipUnless(
        TEST_WITH_LOCAL_SERVER, "Tests using local websocket server are disabled"
    )
    def test_sockopt(self):
        sockopt = ((socket.IPPROTO_TCP, socket.TCP_NODELAY, 1),)
        s = ws.create_connection(
            f"ws://127.0.0.1:{LOCAL_WS_SERVER_PORT}", sockopt=sockopt
        )
        self.assertNotEqual(
            s.sock.getsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY), 0
        )
        s.close()


class UtilsTest(unittest.TestCase):
    def test_utf8_validator(self):
        state = validate_utf8(b"\xf0\x90\x80\x80")
        self.assertEqual(state, True)
        state = validate_utf8(
            b"\xce\xba\xe1\xbd\xb9\xcf\x83\xce\xbc\xce\xb5\xed\xa0\x80edited"
        )
        self.assertEqual(state, False)
        state = validate_utf8(b"")
        self.assertEqual(state, True)
        state = validate_utf8("κόσμε")
        self.assertEqual(state, True)
        state = validate_utf8("a\ud800b")
        self.assertEqual(state, False)
        state = validate_utf8("")
        self.assertEqual(state, True)


class HandshakeTest(unittest.TestCase):
    def test_connect_ignores_invalid_cookie(self):
        sock = SockMock()
        sock.add_packet(
            b"HTTP/1.1 101 Switching Protocols\r\n"
            b"Connection: Upgrade\r\n"
            b"Upgrade: websocket\r\n"
            b"Sec-WebSocket-Accept: Kxep+hNu9n51529fGidYu7a3wO0=\r\n"
            b"Set-Cookie: bad@name=secret-value; domain=example.com\r\n\r\n"
        )
        cookie_jar = SimpleCookieJar()
        cookie_jar.add("existing=preserved; domain=example.com")
        with mock.patch("websocket._handshake.CookieJar", cookie_jar), mock.patch(
            "websocket._handshake._create_sec_websocket_key",
            return_value="c6b8hTg4EeGb2gQMztV1/g==",
        ), self.assertLogs("websocket", level="WARNING") as logs:
            websock = ws.create_connection("ws://example.com/", socket=sock)
        try:
            self.assertTrue(websock.connected)
            self.assertEqual(websock.getstatus(), 101)
            self.assertEqual(cookie_jar.get("example.com"), "existing=preserved")
            self.assertEqual(
                logs.output, ["WARNING:websocket:Ignoring invalid Set-Cookie header"]
            )
        finally:
            websock.shutdown()

    def test_redirect_ignores_invalid_cookie(self):
        headers = {"location": "ws://example.com/", "set-cookie": "bad@name=value"}
        with mock.patch(
            "websocket._handshake.CookieJar", SimpleCookieJar()
        ), self.assertLogs("websocket", level="WARNING"):
            response = handshake_response(302, headers, None)
        self.assertEqual(response.status, 302)
        self.assertEqual(response.headers, headers)

    def test_cookiejar_rejects_cross_host_domain(self):
        jar = SimpleCookieJar()
        jar.add("fixated=1; Domain=good.com", host="evil.com")
        self.assertEqual(jar.get("good.com"), "")

    def test_cookiejar_allows_own_and_parent_domain(self):
        jar = SimpleCookieJar()
        jar.add("self=1; Domain=sub.example.com", host="sub.example.com")
        jar.add("parent=1; Domain=example.com", host="sub.example.com")
        self.assertEqual(jar.get("sub.example.com"), "parent=1; self=1")
        self.assertEqual(jar.get("example.com"), "parent=1")

    def test_cookiejar_rejects_single_label_domain(self):
        jar = SimpleCookieJar()
        jar.add("s=1; Domain=com", host="example.com")
        self.assertEqual(jar.get("example.com"), "")

    def test_cookiejar_invalid_cookie_does_not_block_valid(self):
        jar = SimpleCookieJar()
        with self.assertLogs("websocket", level="WARNING"):
            jar.add(["bad@name=1", "good=1; Domain=example.com"], host="example.com")
        self.assertEqual(jar.get("example.com"), "good=1")

    def test_handshake_scopes_set_cookie_to_responding_host(self):
        sock = SockMock()
        sock.add_packet(
            b"HTTP/1.1 101 Switching Protocols\r\n"
            b"Connection: Upgrade\r\n"
            b"Upgrade: websocket\r\n"
            b"Sec-WebSocket-Accept: Kxep+hNu9n51529fGidYu7a3wO0=\r\n"
            b"Set-Cookie: fixated=1; Domain=other.com\r\n"
            b"Set-Cookie: session=1; Domain=example.com\r\n\r\n"
        )
        jar = SimpleCookieJar()
        with mock.patch("websocket._handshake.CookieJar", jar), mock.patch(
            "websocket._handshake._create_sec_websocket_key",
            return_value="c6b8hTg4EeGb2gQMztV1/g==",
        ):
            websock = ws.create_connection("ws://example.com/", socket=sock)
        try:
            self.assertEqual(jar.get("other.com"), "")
            self.assertEqual(jar.get("example.com"), "session=1")
        finally:
            websock.shutdown()

    def test_bad_status_exception_carries_status_message(self):
        exc = WebSocketBadStatusException(
            "Handshake status 404 Not Found", 404, "Not Found"
        )
        self.assertEqual(exc.status_code, 404)
        self.assertEqual(exc.status_message, "Not Found")
        self.assertIsNone(exc.resp_headers)
        self.assertIsNone(exc.resp_body)

    @unittest.skipUnless(TEST_WITH_INTERNET, "Internet-requiring tests are disabled")
    def test_http_ssl(self):
        websock1 = ws.WebSocket(
            sslopt={"cert_chain": ssl.get_default_verify_paths().capath},
            enable_multithread=False,
        )
        self.assertRaises(ValueError, websock1.connect, "wss://api.bitfinex.com/ws/2")
        websock2 = ws.WebSocket(sslopt={"certfile": "myNonexistentCertFile"})
        self.assertRaises(
            WebSocketException, websock2.connect, "wss://api.bitfinex.com/ws/2"
        )

    @unittest.skipUnless(TEST_WITH_INTERNET, "Internet-requiring tests are disabled")
    def test_manual_headers(self):
        websock3 = ws.WebSocket(
            sslopt={
                "ca_certs": ssl.get_default_verify_paths().cafile,
                "ca_cert_path": ssl.get_default_verify_paths().capath,
            }
        )
        self.assertRaises(
            WebSocketBadStatusException,
            websock3.connect,
            "wss://api.bitfinex.com/ws/2",
            cookie="chocolate",
            origin="testing_websockets.com",
            host="echo.websocket.events/websocket-client-test",
            subprotocols=["testproto"],
            connection="Upgrade",
            header={
                "CustomHeader1": "123",
                "Cookie": "TestValue",
                "Sec-WebSocket-Key": "k9kFAUWNAMmf5OEMfTlOEA==",
                "Sec-WebSocket-Protocol": "newprotocol",
            },
        )

    def test_ipv6(self):
        websock2 = ws.WebSocket()
        self.assertRaises(ValueError, websock2.connect, "2001:4860:4860::8888")

    def test_bad_urls(self):
        websock3 = ws.WebSocket()
        self.assertRaises(ValueError, websock3.connect, "ws//example.com")
        self.assertRaises(WebSocketAddressException, websock3.connect, "ws://example")
        self.assertRaises(ValueError, websock3.connect, "example.com")

    def test_suppress_host_header(self):
        """Test suppress_host parameter in _get_handshake_headers function"""
        # Test normal behavior (Host header included)
        headers, key = _get_handshake_headers(
            "/path", "ws://example.com:8080", "example.com", 8080, {}
        )
        host_headers = [h for h in headers if h.startswith("Host:")]
        self.assertEqual(len(host_headers), 1)
        self.assertEqual(host_headers[0], "Host: example.com:8080")

        # Test suppress_host=False (explicit, should still include Host header)
        headers, key = _get_handshake_headers(
            "/path",
            "ws://example.com:8080",
            "example.com",
            8080,
            {"suppress_host": False},
        )
        host_headers = [h for h in headers if h.startswith("Host:")]
        self.assertEqual(len(host_headers), 1)
        self.assertEqual(host_headers[0], "Host: example.com:8080")

        # Test suppress_host=True (Host header should be suppressed)
        headers, key = _get_handshake_headers(
            "/path",
            "ws://example.com:8080",
            "example.com",
            8080,
            {"suppress_host": True},
        )
        host_headers = [h for h in headers if h.startswith("Host:")]
        self.assertEqual(len(host_headers), 0)

        # Test with custom host header and suppress_host=False
        headers, key = _get_handshake_headers(
            "/path",
            "ws://example.com:8080",
            "example.com",
            8080,
            {"host": "custom-host.example.com", "suppress_host": False},
        )
        host_headers = [h for h in headers if h.startswith("Host:")]
        self.assertEqual(len(host_headers), 1)
        self.assertEqual(host_headers[0], "Host: custom-host.example.com")

        # Test with custom host header and suppress_host=True (should suppress even custom host)
        headers, key = _get_handshake_headers(
            "/path",
            "ws://example.com:8080",
            "example.com",
            8080,
            {"host": "custom-host.example.com", "suppress_host": True},
        )
        host_headers = [h for h in headers if h.startswith("Host:")]
        self.assertEqual(len(host_headers), 0)

        # Test with standard ports (80, 443) - should not include port in host
        headers, key = _get_handshake_headers(
            "/path", "ws://example.com", "example.com", 80, {}
        )
        host_headers = [h for h in headers if h.startswith("Host:")]
        self.assertEqual(len(host_headers), 1)
        self.assertEqual(host_headers[0], "Host: example.com")

        # Test suppress_host=True with standard port
        headers, key = _get_handshake_headers(
            "/path", "ws://example.com", "example.com", 80, {"suppress_host": True}
        )
        host_headers = [h for h in headers if h.startswith("Host:")]
        self.assertEqual(len(host_headers), 0)

    def test_sec_websocket_key_from_list_header(self):
        """A custom key passed as a list entry must not be duplicated."""
        custom_key = "k9kFAUWNAMmf5OEMfTlOEA=="
        headers, key = _get_handshake_headers(
            "/",
            "ws://example.com",
            "example.com",
            80,
            {"header": [f"Sec-WebSocket-Key: {custom_key}"]},
        )
        self.assertEqual(
            [h for h in headers if h.startswith("Sec-WebSocket-Key:")],
            [f"Sec-WebSocket-Key: {custom_key}"],
        )
        self.assertEqual(key, custom_key)

    def test_sec_websocket_key_dict_header_case_and_none(self):
        # lowercase dict entry is honored; explicit None means "not specified"
        headers, key = _get_handshake_headers(
            "/",
            "ws://example.com",
            "example.com",
            80,
            {"header": {"sec-websocket-key": "abc123"}},
        )
        self.assertEqual(
            [h for h in headers if h.lower().startswith("sec-websocket-key:")],
            ["sec-websocket-key: abc123"],
        )
        self.assertEqual(key, "abc123")

        headers, key = _get_handshake_headers(
            "/",
            "ws://example.com",
            "example.com",
            80,
            {"header": {"Sec-WebSocket-Key": None}},
        )
        key_headers = [h for h in headers if h.startswith("Sec-WebSocket-Key:")]
        self.assertEqual(len(key_headers), 1)
        self.assertEqual(key_headers[0], f"Sec-WebSocket-Key: {key}")
        self.assertNotIn("None", key)

    def test_host_port_elision_follows_scheme(self):
        # the port is omitted only for the scheme's own default port
        headers, _ = _get_handshake_headers(
            "/", "ws://example.com:443", "example.com", 443, {}
        )
        self.assertIn("Host: example.com:443", headers)
        self.assertIn("Origin: http://example.com:443", headers)

        headers, _ = _get_handshake_headers(
            "/", "wss://example.com:80", "example.com", 80, {}
        )
        self.assertIn("Host: example.com:80", headers)

        headers, _ = _get_handshake_headers(
            "/", "wss://example.com", "example.com", 443, {}
        )
        self.assertIn("Host: example.com", headers)

    def test_handshake_values_reject_crlf_and_nul(self):
        """CR, LF or NUL in a caller-supplied handshake value would end the
        header line and inject headers of its own. The handshake raises before
        sending anything, and the error does not echo the value."""
        injected = "x\r\nInjected: yes"
        cases = {
            "header list": {"header": [f"X-A: {injected}"]},
            "header dict value": {"header": {"X-A": injected}},
            "header dict name": {"header": {injected: "1"}},
            "subprotocols": {"subprotocols": ["chat", injected]},
            "origin": {"origin": injected},
            "host": {"host": injected},
            "cookie": {"cookie": f"a={injected}"},
            "connection": {"connection": f"Connection: Upgrade{injected}"},
            "lone LF": {"origin": "http://o\nInjected: yes"},
            "lone CR": {"origin": "http://o\rInjected: yes"},
            "NUL": {"origin": "http://o\0Injected"},
        }
        for label, options in cases.items():
            with self.subTest(label):
                sock = SockMock()
                with self.assertRaisesRegex(ws.WebSocketException, "not allowed"):
                    ws.create_connection("ws://example.com/", socket=sock, **options)
                self.assertEqual(sock.sent, [])

        with self.assertRaises(ws.WebSocketException) as cm:
            _get_handshake_headers(
                "/", "ws://example.com", "example.com", 80, {"cookie": "s=SECRET\r\n"}
            )
        self.assertIn("'cookie'", str(cm.exception))
        self.assertNotIn("SECRET", str(cm.exception))

        # Ordinary values are sent exactly as before
        with mock.patch.dict(CookieJar.jar, clear=True):
            headers, _ = _get_handshake_headers(
                "/",
                "ws://example.com",
                "example.com",
                80,
                {
                    "header": {"X-A": "1", "X-Skipped": None},
                    "subprotocols": ["chat", "v2"],
                    "origin": "http://o",
                    "host": "h:81",
                    "cookie": "a=b",
                    "connection": "Connection: Upgrade, keep-alive",
                },
            )
        for line in (
            "Host: h:81",
            "Origin: http://o",
            "Connection: Upgrade, keep-alive",
            "Sec-WebSocket-Protocol: chat,v2",
            "X-A: 1",
            "Cookie: a=b",
        ):
            self.assertIn(line, headers)

    def test_handshake_rejects_header_entries_that_are_not_lines(self):
        """An empty entry in a list header ends the request's header block
        early, so later headers and the Cookie line are sent after the request
        (N166); an entry without a name or ':' is not a header line either. The
        handshake raises before sending anything, without echoing the entry."""
        for entry in ("", "   ", "Bearer SECRET", ": SECRET"):
            with self.subTest(entry=entry):
                sock = SockMock()
                with self.assertRaisesRegex(
                    ws.WebSocketException, "Invalid 'header' option"
                ) as cm:
                    ws.create_connection(
                        "ws://example.com/",
                        socket=sock,
                        header=["X-A: 1", entry, "X-B: 2"],
                    )
                self.assertNotIn("SECRET", str(cm.exception))
                self.assertEqual(sock.sent, [])

    def test_trace_redacts_credentials(self):
        """enableTrace must not log credential values: Authorization and Cookie
        in the handshake request, Set-Cookie in the response, and the CONNECT
        Proxy-Authorization. The wire still carries the real values."""
        stream = io.StringIO()
        ws.enableTrace(True, handler=logging.StreamHandler(stream))
        self.addCleanup(ws.enableTrace, False)

        sock = SockMock()
        sock.add_packet(
            b"HTTP/1.1 101 Switching Protocols\r\n"
            b"Connection: Upgrade\r\n"
            b"Upgrade: websocket\r\n"
            b"Sec-WebSocket-Accept: Kxep+hNu9n51529fGidYu7a3wO0=\r\n"
            b"Set-Cookie: session=SETCOOKIESECRET; domain=example.com\r\n\r\n"
        )
        with mock.patch(
            "websocket._handshake.CookieJar", SimpleCookieJar()
        ), mock.patch(
            "websocket._handshake._create_sec_websocket_key",
            return_value="c6b8hTg4EeGb2gQMztV1/g==",
        ):
            websock = ws.create_connection(
                "ws://example.com/",
                socket=sock,
                header=["authorization: Bearer BEARERSECRET", "X-Trace: visible"],
                cookie="sid=COOKIESECRET",
            )
        websock.shutdown()

        tunnel_sock = SockMock()
        tunnel_sock.add_packet(b"HTTP/1.1 200 Connection Established\r\n\r\n")
        _tunnel(tunnel_sock, "example.com", 443, ("proxyuser", "PROXYSECRET"))
        proxy_credentials = base64encode(b"proxyuser:PROXYSECRET").decode().strip()

        logged = stream.getvalue()
        for secret in (
            "BEARERSECRET",
            "COOKIESECRET",
            "SETCOOKIESECRET",
            proxy_credentials,
        ):
            self.assertNotIn(secret, logged)
        for line in (
            "authorization: [redacted]",
            "Cookie: [redacted]",
            "Set-Cookie: [redacted]",
            "Proxy-Authorization: [redacted]",
            "X-Trace: visible",
        ):
            self.assertIn(line, logged)

        sent = b"".join(sock.sent) + b"".join(tunnel_sock.sent)
        for secret in (b"BEARERSECRET", b"COOKIESECRET", proxy_credentials.encode()):
            self.assertIn(secret, sent)

    def test_trace_redacts_url_query_and_location_credentials(self):
        """Tokens often travel in the URL query (AWS presigned URLs, Azure Web
        PubSub access_token) or a redirect's query (OAuth code). The trace keeps
        the path but not the query, and a Location loses its userinfo (N172)."""
        stream = io.StringIO()
        ws.enableTrace(True, handler=logging.StreamHandler(stream))
        self.addCleanup(ws.enableTrace, False)

        sock = SockMock()
        sock.add_packet(
            b"HTTP/1.1 302 Found\r\n"
            b"Location: ws://user:PWSECRET@example.com/cb?code=CODESECRET\r\n"
            b"Content-Length: 0\r\n\r\n"
        )
        with self.assertRaisesRegex(ws.WebSocketException, "Redirect limit exhausted"):
            ws.WebSocket().connect(
                "ws://example.com/ws?access_token=QUERYSECRET",
                socket=sock,
                redirect_limit=0,
            )

        logged = stream.getvalue()
        for secret in ("QUERYSECRET", "PWSECRET", "CODESECRET"):
            self.assertNotIn(secret, logged)
        self.assertIn("GET /ws?[redacted] HTTP/1.1", logged)
        self.assertIn("Location: ws://example.com/cb?[redacted]", logged)
        self.assertIn(b"QUERYSECRET", b"".join(sock.sent))

    def test_handshake_cookie_from_multiple_set_cookie(self):
        """Cookies received as two Set-Cookie headers must reach the next
        handshake's Cookie header uncontaminated (one per domain)."""
        with mock.patch.dict(CookieJar.jar, clear=True):
            sock = SockMock()
            sock.add_packet(
                b"HTTP/1.1 101 Switching Protocols\r\n"
                b"Set-Cookie: session=x; Domain=.example.com\r\n"
                b"Set-Cookie: tracking=y; Domain=.ads.example.com\r\n"
                b"\r\n"
            )
            _, header, _ = read_headers(sock)
            handshake_response(101, header, None)

            headers, _ = _get_handshake_headers(
                "/", "ws://example.com", "example.com", 80, {}
            )
            self.assertEqual(
                [h for h in headers if h.startswith("Cookie:")],
                ["Cookie: session=x"],
            )

    def test_suppress_host_websocket_connect(self):
        """Test suppress_host parameter with WebSocket.connect()"""
        websock = ws.WebSocket()

        # Test that suppress_host parameter is accepted without error
        # (Connection will fail but parameter should be accepted)
        try:
            websock.connect(
                "ws://nonexistent.example.com", suppress_host=True, timeout=0.1
            )
        except (WebSocketAddressException, OSError, socket.timeout):
            # Expected - connection should fail, but parameter was accepted
            pass

        # Test that suppress_host=False also works
        try:
            websock.connect(
                "ws://nonexistent.example.com", suppress_host=False, timeout=0.1
            )
        except (WebSocketAddressException, OSError, socket.timeout):
            # Expected - connection should fail, but parameter was accepted
            pass


class WebSocketCoreUnitTests(unittest.TestCase):
    def test_iteration_helpers_and_next_aliases(self):
        class TestError(Exception):
            pass

        sock = ws.WebSocket()
        sock.recv = mock.Mock(side_effect=["first", TestError("stop")])

        iterator = iter(sock)
        self.assertEqual(next(iterator), "first")
        with self.assertRaises(TestError):
            next(iterator)

        sock.recv = mock.Mock(return_value="again")
        self.assertEqual(sock.__next__(), "again")
        self.assertEqual(sock.next(), "again")

    def test_fileno_requires_socket(self):
        sock = ws.WebSocket()
        with self.assertRaises(WebSocketException):
            sock.fileno()

        fake_socket = mock.Mock()
        fake_socket.fileno.return_value = 42
        sock.sock = fake_socket
        self.assertEqual(sock.fileno(), 42)

    def test_close_after_peer_disconnect_frees_socket(self):
        """#1066: close() on a connection the peer already dropped frees the fd."""
        sock = ws.WebSocket()
        fake_socket = mock.Mock()
        fake_socket._closed = False
        sock.sock = fake_socket
        sock.connected = False

        sock.close()

        fake_socket.close.assert_called_once_with()
        self.assertIsNone(sock.sock)

    def test_concurrent_close_keeps_close_handshake(self):
        """A second close() while another thread waits for the peer's close
        frame must not shut the socket down underneath it (#1066 regression)."""
        client, peer = socket.socketpair()
        self.addCleanup(peer.close)
        sock = ws.WebSocket()
        sock.sock = client
        sock.connected = True

        closer = threading.Thread(target=sock.close, kwargs={"timeout": 5})
        closer.start()
        peer.settimeout(5)
        self.assertEqual(peer.recv(2)[0], 0x88)  # the client's CLOSE frame arrived

        sock.close()  # e.g. run_forever's teardown racing app.close()
        peer.sendall(b"\x88\x05" + struct.pack("!H", 4001) + b"bye")
        closer.join(5)

        self.assertFalse(closer.is_alive())
        self.assertIsNotNone(sock.close_frame)
        self.assertEqual(sock.close_frame.data, struct.pack("!H", 4001) + b"bye")
        self.assertIsNone(sock.sock)

    def test_settimeout_updates_underlying_socket(self):
        sock = ws.WebSocket()
        fake_socket = mock.Mock()
        sock.sock = fake_socket

        sock.settimeout(5)
        self.assertEqual(sock.gettimeout(), 5)
        fake_socket.settimeout.assert_called_once_with(5)

    def test_settimeout_rejects_bool_and_nonfinite(self):
        """bool subclasses int; True must not become a 1s socket timeout."""
        sock = ws.WebSocket()
        for value in (True, False):
            with self.assertRaises(TypeError):
                sock.settimeout(value)
        for value in (float("nan"), float("inf"), float("-inf")):
            with self.assertRaises(ValueError):
                sock.settimeout(value)
        sock.settimeout(None)
        self.assertIsNone(sock.gettimeout())
        sock.settimeout(2.5)
        self.assertEqual(sock.gettimeout(), 2.5)

    def test_connect_rejects_bool_and_nonfinite_timeout(self):
        """connect(timeout=...) is validated like settimeout(), before any socket opens."""
        cases = [(True, TypeError), (False, TypeError), ("5", TypeError)]
        cases += [(v, ValueError) for v in (float("nan"), float("inf"), float("-inf"))]
        for value, exc in cases:
            with self.subTest(timeout=value):
                sock = ws.WebSocket()
                with mock.patch("websocket._core.connect") as connect_mock:
                    with self.assertRaises(exc):
                        sock.connect("ws://example.com", timeout=value)
                connect_mock.assert_not_called()
                self.assertIsNone(sock.gettimeout())

    def test_is_ssl_detection(self):
        sock = ws.WebSocket()
        self.assertFalse(sock.is_ssl())

        class FakeSSLSocket:
            pass

        with mock.patch("websocket._core.ssl.SSLSocket", FakeSSLSocket):
            sock.sock = FakeSSLSocket()
            self.assertTrue(sock.is_ssl())

    def test_send_frame_emits_trace_when_enabled(self):
        sock = ws.WebSocket()
        sock._send = mock.Mock(side_effect=lambda data: len(data))
        sock.lock = mock.MagicMock()

        frame = ABNF.create_frame("hi", ABNF.OPCODE_TEXT)

        with mock.patch(
            "websocket._core.isEnabledForTrace", return_value=True
        ), mock.patch("websocket._core.trace") as trace_mock:
            length = sock.send_frame(frame)

        self.assertGreater(length, 0)
        self.assertEqual(trace_mock.call_count, 2)

    def test_connect_handles_redirects(self):
        sock = ws.WebSocket()
        first_socket = mock.Mock()
        second_socket = mock.Mock()
        connect_results = [
            (first_socket, ("origin", 80, "/")),
            (second_socket, ("redirect", 80, "/")),
        ]

        def fake_connect(url, *_):
            return connect_results.pop(0)

        redirect_resp = handshake_response(301, {"location": "ws://redirect"}, None)
        success_resp = handshake_response(101, {}, None)

        with mock.patch(
            "websocket._core.connect", side_effect=fake_connect
        ) as connect_mock, mock.patch(
            "websocket._core.handshake", side_effect=[redirect_resp, success_resp]
        ) as handshake_mock:
            sock.connect("ws://origin", redirect_limit=1)

        self.assertTrue(sock.connected)
        self.assertIs(sock.sock, second_socket)
        first_socket.close.assert_called_once()
        self.assertEqual(
            [call.args[0] for call in connect_mock.call_args_list],
            ["ws://origin", "ws://redirect"],
        )
        self.assertEqual(handshake_mock.call_count, 2)

    def test_connect_cross_authority_redirect_strips_credentials(self):
        sock = ws.WebSocket()
        connect_results = [
            (mock.Mock(), ("origin", 80, "/")),
            (mock.Mock(), ("redirect", 80, "/")),
        ]

        def fake_connect(url, *_):
            return connect_results.pop(0)

        redirect_resp = handshake_response(302, {"location": "ws://redirect"}, None)
        success_resp = handshake_response(101, {}, None)

        with mock.patch(
            "websocket._core.connect", side_effect=fake_connect
        ), mock.patch(
            "websocket._core.handshake", side_effect=[redirect_resp, success_resp]
        ) as handshake_mock:
            sock.connect(
                "ws://origin",
                header=[
                    "Authorization: Bearer t",
                    "Proxy-Authorization: Basic cDpx",
                    "Cookie: session=abc",
                    "Host: a.internal",
                    "X-Custom: v",
                ],
                cookie="session=abc",
                host="a.internal",
                redirect_limit=1,
            )

        first, redirected = handshake_mock.call_args_list
        self.assertEqual(first.kwargs["host"], "a.internal")
        self.assertNotIn("cookie", redirected.kwargs)
        self.assertNotIn("host", redirected.kwargs)
        self.assertEqual(redirected.kwargs["header"], ["X-Custom: v"])
        # hop 2 announces the redirect target, not the original authority
        hop2_headers, _ = _get_handshake_headers(
            "/", "ws://redirect", "redirect", 80, redirected.kwargs
        )
        self.assertEqual(
            [h for h in hop2_headers if h.startswith("Host")], ["Host: redirect"]
        )

    def test_connect_cross_authority_redirect_strips_dict_credentials(self):
        sock = ws.WebSocket()
        connect_results = [
            (mock.Mock(), ("origin", 80, "/")),
            (mock.Mock(), ("redirect", 80, "/")),
        ]

        def fake_connect(url, *_):
            return connect_results.pop(0)

        redirect_resp = handshake_response(301, {"location": "ws://redirect"}, None)
        success_resp = handshake_response(101, {}, None)

        with mock.patch(
            "websocket._core.connect", side_effect=fake_connect
        ), mock.patch(
            "websocket._core.handshake", side_effect=[redirect_resp, success_resp]
        ) as handshake_mock:
            sock.connect(
                "ws://origin",
                header={
                    "Authorization ": "Bearer t",
                    "proxy-authorization": "Basic cDpx",
                    "Cookie": "session=abc",
                    "HOST": "a.internal",
                    "X-Custom": "v",
                },
                cookie="session=abc",
                redirect_limit=1,
            )

        redirected = handshake_mock.call_args_list[1]
        self.assertEqual(redirected.kwargs["header"], {"X-Custom": "v"})

    def test_connect_same_authority_redirect_keeps_credentials(self):
        sock = ws.WebSocket()
        connect_results = [
            (mock.Mock(), ("origin", 80, "/")),
            (mock.Mock(), ("origin", 80, "/new")),
        ]

        def fake_connect(url, *_):
            return connect_results.pop(0)

        redirect_resp = handshake_response(302, {"location": "ws://origin/new"}, None)
        success_resp = handshake_response(101, {}, None)

        with mock.patch(
            "websocket._core.connect", side_effect=fake_connect
        ), mock.patch(
            "websocket._core.handshake", side_effect=[redirect_resp, success_resp]
        ) as handshake_mock:
            sock.connect(
                "ws://origin",
                header=["Authorization: Bearer t"],
                cookie="session=abc",
                host="a.internal",
                redirect_limit=1,
            )

        redirected = handshake_mock.call_args_list[1]
        self.assertEqual(redirected.kwargs["header"], ["Authorization: Bearer t"])
        self.assertEqual(redirected.kwargs["cookie"], "session=abc")
        self.assertEqual(redirected.kwargs["host"], "a.internal")

    def test_connect_redirect_limit_exhausted_raises(self):
        sock = ws.WebSocket()
        sockets = []
        redirect_resp = handshake_response(302, {"location": "ws://redirect"}, None)

        def fake_connect(url, *args, **kwargs):
            socket_mock = mock.Mock()
            sockets.append(socket_mock)
            return socket_mock, ("redirect", 80, "/")

        with mock.patch(
            "websocket._core.connect", side_effect=fake_connect
        ) as connect_mock, mock.patch(
            "websocket._core.handshake", return_value=redirect_resp
        ):
            with self.assertRaisesRegex(
                ws.WebSocketException, "Redirect limit exhausted"
            ):
                sock.connect("ws://origin", redirect_limit=2)

        self.assertEqual(connect_mock.call_count, 3)
        self.assertFalse(sock.connected)
        self.assertIsNone(sock.sock)
        for socket_mock in sockets:
            socket_mock.close.assert_called_once()

    def test_connect_redirect_invalid_target_raises(self):
        sock = ws.WebSocket()
        redirect_resp = handshake_response(302, {"location": "https://redirect"}, None)

        def fake_connect(url, *args, **kwargs):
            if url == "https://redirect":
                raise ValueError("scheme https is invalid")
            return mock.Mock(), ("origin", 80, "/")

        with mock.patch(
            "websocket._core.connect", side_effect=fake_connect
        ), mock.patch("websocket._core.handshake", return_value=redirect_resp):
            with self.assertRaisesRegex(
                ws.WebSocketException, "Invalid redirect target https://redirect"
            ):
                sock.connect("ws://origin", redirect_limit=2)

        self.assertFalse(sock.connected)
        self.assertIsNone(sock.sock)

    def test_connect_refuses_wss_to_ws_redirect(self):
        sock = ws.WebSocket()
        first_socket = mock.Mock()
        redirect_resp = handshake_response(302, {"location": "ws://redirect/"}, None)

        with mock.patch(
            "websocket._core.connect", return_value=(first_socket, ("origin", 443, "/"))
        ) as connect_mock, mock.patch(
            "websocket._core.handshake", return_value=redirect_resp
        ):
            with self.assertRaisesRegex(ws.WebSocketException, "downgrade"):
                sock.connect("wss://origin/", redirect_limit=2)

        self.assertEqual(
            [call.args[0] for call in connect_mock.call_args_list], ["wss://origin/"]
        )
        first_socket.close.assert_called_once()
        self.assertFalse(sock.connected)
        self.assertIsNone(sock.sock)

    def test_downgrade_refusal_message_hides_credentials(self):
        """The refusal names only scheme://host:port of both URLs: the caller's
        userinfo, path and query (tokens) must not reach logged exceptions."""
        sock = ws.WebSocket()
        redirect_resp = handshake_response(
            302, {"location": "ws://loc-user:loc-pw@redirect:8080/p?t=LOCTOKEN"}, None
        )
        with mock.patch(
            "websocket._core.connect", return_value=(mock.Mock(), ("origin", 8443, "/"))
        ), mock.patch("websocket._core.handshake", return_value=redirect_resp):
            with self.assertRaises(ws.WebSocketException) as cm:
                sock.connect(
                    "wss://svc-user:Pa55w0rd@origin:8443/stream?access_token=SECRET",
                    redirect_limit=2,
                )
        message = str(cm.exception)
        self.assertIn("wss://origin:8443", message)
        self.assertIn("ws://redirect:8080", message)
        for secret in (
            "svc-user",
            "Pa55w0rd",
            "SECRET",
            "/stream",
            "loc-pw",
            "LOCTOKEN",
        ):
            self.assertNotIn(secret, message)

    def test_connect_follows_ws_to_wss_redirect(self):
        sock = ws.WebSocket()
        connect_results = [
            (mock.Mock(), ("origin", 80, "/")),
            (mock.Mock(), ("redirect", 443, "/")),
        ]
        redirect_resp = handshake_response(302, {"location": "wss://redirect/"}, None)
        success_resp = handshake_response(101, {}, None)

        with mock.patch(
            "websocket._core.connect", side_effect=lambda *a: connect_results.pop(0)
        ) as connect_mock, mock.patch(
            "websocket._core.handshake", side_effect=[redirect_resp, success_resp]
        ):
            sock.connect("ws://origin/", redirect_limit=2)

        self.assertTrue(sock.connected)
        self.assertEqual(
            [call.args[0] for call in connect_mock.call_args_list],
            ["ws://origin/", "wss://redirect/"],
        )

    def test_connect_redirect_without_location_raises(self):
        sock = ws.WebSocket()
        redirect_resp = handshake_response(302, {}, None)  # no location header

        def fake_connect(url, *args, **kwargs):
            return mock.Mock(), ("origin", 80, "/")

        with mock.patch(
            "websocket._core.connect", side_effect=fake_connect
        ), mock.patch("websocket._core.handshake", return_value=redirect_resp):
            with self.assertRaisesRegex(ws.WebSocketException, "Location"):
                sock.connect("ws://origin", redirect_limit=2)

        self.assertFalse(sock.connected)
        self.assertIsNone(sock.sock)

    def test_connect_with_caller_socket_does_not_follow_redirect(self):
        """A redirect on a caller-supplied socket (an SSH or Tor tunnel, a unix
        socket) must not make the client dial the new location directly, outside
        that tunnel and with the caller's credentials."""
        target = socket.socket()
        target.bind(("127.0.0.1", 0))
        target.listen()
        target.settimeout(0.2)
        self.addCleanup(target.close)
        target_port = target.getsockname()[1]

        tunnel, peer = socket.socketpair()
        self.addCleanup(peer.close)
        # a stalled answerer must fail the test, not hang the suite
        tunnel.settimeout(5)

        def answer_302():
            peer.recv(65536)
            peer.sendall(
                b"HTTP/1.1 302 Found\r\n"
                + f"Location: ws://user:pw@127.0.0.1:{target_port}/x?t=1\r\n".encode()
                + b"Content-Length: 0\r\n\r\n"
            )

        server = threading.Thread(target=answer_302, daemon=True)
        server.start()
        websock = ws.WebSocket()
        with self.assertRaisesRegex(
            ws.WebSocketException,
            rf"Redirect \(status 302\) to ws://127\.0\.0\.1:{target_port} not followed",
        ):
            websock.connect(
                "ws://example.com/",
                socket=tunnel,
                header=["Authorization: Bearer SECRET"],
                timeout=2,  # if the redirect is followed, fail instead of hanging
            )
        server.join(5)

        with self.assertRaises(socket.timeout):
            target.accept()
        self.assertFalse(websock.connected)
        self.assertIsNone(websock.sock)

    def test_malformed_redirect_location_raises_websocket_exception(self):
        """A server-controlled Location that urlparse rejects must raise
        WebSocketException on every path (N149), and the target in the message
        must not carry its path or query (N148)."""

        def answer_302(peer, location):
            peer.recv(65536)
            peer.sendall(
                b"HTTP/1.1 302 Found\r\n"
                + f"Location: {location}\r\n".encode()
                + b"Content-Length: 0\r\n\r\n"
            )

        for location in (
            "ws://[::1/x",
            # parse errors quote everything before the first ":", which here
            # includes the query
            "/cb?code=SECRET&redirect_uri=https://app.example/",
            "//idp.example/cb?code=SECRET&redirect_uri=https://app.example/",
        ):
            with self.subTest(location=location, path="caller socket"):
                # connect() closes the caller socket when it raises, so each
                # subTest needs a fresh one
                tunnel, peer = socket.socketpair()
                self.addCleanup(peer.close)
                # a stalled answerer must fail the test, not hang the suite
                tunnel.settimeout(5)
                server = threading.Thread(
                    target=answer_302, args=(peer, location), daemon=True
                )
                server.start()
                websock = ws.WebSocket()
                with self.assertRaises(ws.WebSocketException) as caught:
                    websock.connect("ws://example.com/", socket=tunnel, timeout=2)
                self.assertNotIn("SECRET", str(caught.exception))
                self.assertNotIn("to ://", str(caught.exception))
                self.assertNotIsInstance(caught.exception, ws.WebSocketTimeoutException)
                server.join(5)

        # the wss->ws downgrade check parses Location too
        redirect_resp = handshake_response(302, {"location": "ws://[::1/x"}, None)
        with mock.patch(
            "websocket._core.connect", return_value=(mock.Mock(), ("origin", 443, "/"))
        ), mock.patch("websocket._core.handshake", return_value=redirect_resp):
            with self.assertRaisesRegex(
                ws.WebSocketException, "Invalid redirect target <invalid URL>"
            ):
                ws.WebSocket().connect("wss://origin/")

        # a Location that is not a ws/wss URL is refused with a fixed message
        redirect_resp = handshake_response(
            302, {"location": "https://idp.example/cb?code=SECRET"}, None
        )
        with mock.patch(
            "websocket._core.connect", return_value=(mock.Mock(), ("origin", 80, "/"))
        ) as connect_mock, mock.patch(
            "websocket._core.handshake", return_value=redirect_resp
        ):
            with self.assertRaisesRegex(
                ws.WebSocketException, r"Invalid redirect target https://idp\.example:"
            ) as caught:
                ws.WebSocket().connect("ws://origin/")
            self.assertNotIn("SECRET", str(caught.exception))
            self.assertEqual(connect_mock.call_count, 1)

        # a ValueError from dialing a valid ws:// target (an IDNA label that is
        # too long) shows only the target's origin
        def first_hop_ok_then_invalid(url, *args, **kwargs):
            if url != "ws://origin/":
                raise UnicodeError("label too long")
            return mock.Mock(), ("origin", 80, "/")

        redirect_resp = handshake_response(
            302, {"location": "ws://idp.example/cb?code=SECRET"}, None
        )
        with mock.patch(
            "websocket._core.connect", side_effect=first_hop_ok_then_invalid
        ), mock.patch("websocket._core.handshake", return_value=redirect_resp):
            with self.assertRaisesRegex(
                ws.WebSocketException,
                r"Invalid redirect target ws://idp\.example: label too long",
            ) as caught:
                ws.WebSocket().connect("ws://origin/")
            self.assertNotIn("SECRET", str(caught.exception))

    def test_explicit_timeout_applies_to_caller_socket(self):
        """An explicit timeout bounds the handshake on a caller-supplied socket
        (N109); without one, the socket keeps its own timeout."""
        cases = (
            # (socket's own timeout, API, options, expected socket timeout)
            (5, "connect", {"timeout": 0.2}, 0.2),
            (5, "create_connection", {"timeout": 0.2}, 0.2),
            (0.2, "connect", {}, 0.2),
            (0.2, "connect", {"timeout": None}, 0.2),
            (0.2, "create_connection", {}, 0.2),
        )
        for own, api, options, expected in cases:
            with self.subTest(own=own, api=api, options=options):
                tunnel, peer = socket.socketpair()  # the peer never answers
                self.addCleanup(tunnel.close)
                self.addCleanup(peer.close)
                tunnel.settimeout(own)
                start = time.monotonic()
                with self.assertRaises(ws.WebSocketTimeoutException):
                    if api == "connect":
                        ws.WebSocket().connect(
                            "ws://example.com/", socket=tunnel, **options
                        )
                    else:
                        ws.create_connection(
                            "ws://example.com/", socket=tunnel, **options
                        )
                self.assertLess(time.monotonic() - start, 2)
                self.assertEqual(tunnel.gettimeout(), expected)

    def test_shutdown_and_abort(self):
        sock = ws.WebSocket()
        socket_mock = mock.Mock()
        socket_mock._closed = False
        sock.sock = socket_mock
        sock.connected = True

        sock.shutdown()
        socket_mock.close.assert_called_once()
        self.assertIsNone(sock.sock)
        self.assertFalse(sock.connected)

        socket_mock = mock.Mock()
        sock.sock = socket_mock
        sock.connected = True
        sock.abort()
        socket_mock.shutdown.assert_called_once_with(socket.SHUT_RDWR)

    def test_abort_tolerates_dead_socket(self):
        sock = ws.WebSocket()
        # never-connected socket: shutdown() raises ENOTCONN
        # which abort() must not leak to the caller
        real = socket.socket()
        sock.sock = real
        sock.connected = True

        sock.abort()  # must not raise
        real.close()

    def test_create_connection_uses_custom_class(self):
        class DummySocket:
            def __init__(self, **kwargs):
                self.init_kwargs = kwargs
                self.timeout_value = None
                self.url = None
                self.options = None

            def settimeout(self, value):
                self.timeout_value = value

            def connect(self, url, **options):
                self.url = url
                self.options = options

        conn = ws.create_connection(
            "ws://example.com",
            timeout=5,
            class_=DummySocket,
            header={"User-Agent": "tester"},
            origin="https://origin",
        )

        self.assertIsInstance(conn, DummySocket)
        self.assertEqual(conn.url, "ws://example.com")
        self.assertEqual(conn.timeout_value, 5)
        self.assertIn("header", conn.options)
        self.assertEqual(conn.options["origin"], "https://origin")


if __name__ == "__main__":
    unittest.main()
