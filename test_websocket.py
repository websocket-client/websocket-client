# -*- coding: utf-8 -*-
#

import base64
import uuid
import unittest

# websocket-client
import websocket as ws

TRACABLE=False

def create_mask_key(n):
    return b"abcd"

class StringSockMock:
    def __init__(self):
        self.set_data("")
        self.sent = []

    def set_data(self, data):
        self.data = data
        self.pos = 0
        self.len = len(data)

    def recv(self, bufsize):
        if self.len < self.pos:
            return
        buf = self.data[self.pos: self.pos + bufsize]
        self.pos += bufsize
        return buf

    def send(self, data):
        self.sent.append(data)

    def close(self):
        pass


class HeaderSockMock(StringSockMock):
    def __init__(self, fname):
        with open(fname, "rb") as f:
            self.set_data(f.read())
        self.sent = []


class WebSocketTest(unittest.TestCase):
    def setUp(self):
        ws.enableTrace(TRACABLE)

    def tearDown(self):
        pass

    def testDefaultTimeout(self):
        self.assertEqual(ws.getdefaulttimeout(), None)
        ws.setdefaulttimeout(10)
        self.assertEqual(ws.getdefaulttimeout(), 10)
        ws.setdefaulttimeout(None)

    def testParseUrl(self):
        p = ws._parse_url("ws://www.example.com/r")
        self.assertEqual(p[0], "www.example.com")
        self.assertEqual(p[1], 80)
        self.assertEqual(p[2], "/r")
        self.assertEqual(p[3], False)

        p = ws._parse_url("ws://www.example.com/r/")
        self.assertEqual(p[0], "www.example.com")
        self.assertEqual(p[1], 80)
        self.assertEqual(p[2], "/r/")
        self.assertEqual(p[3], False)

        p = ws._parse_url("ws://www.example.com/")
        self.assertEqual(p[0], "www.example.com")
        self.assertEqual(p[1], 80)
        self.assertEqual(p[2], "/")
        self.assertEqual(p[3], False)

        p = ws._parse_url("ws://www.example.com")
        self.assertEqual(p[0], "www.example.com")
        self.assertEqual(p[1], 80)
        self.assertEqual(p[2], "/")
        self.assertEqual(p[3], False)

        p = ws._parse_url("ws://www.example.com:8080/r")
        self.assertEqual(p[0], "www.example.com")
        self.assertEqual(p[1], 8080)
        self.assertEqual(p[2], "/r")
        self.assertEqual(p[3], False)

        p = ws._parse_url("ws://www.example.com:8080/")
        self.assertEqual(p[0], "www.example.com")
        self.assertEqual(p[1], 8080)
        self.assertEqual(p[2], "/")
        self.assertEqual(p[3], False)

        p = ws._parse_url("ws://www.example.com:8080")
        self.assertEqual(p[0], "www.example.com")
        self.assertEqual(p[1], 8080)
        self.assertEqual(p[2], "/")
        self.assertEqual(p[3], False)

        p = ws._parse_url("wss://www.example.com:8080/r")
        self.assertEqual(p[0], "www.example.com")
        self.assertEqual(p[1], 8080)
        self.assertEqual(p[2], "/r")
        self.assertEqual(p[3], True)

        p = ws._parse_url("wss://www.example.com:8080/r?key=value")
        self.assertEqual(p[0], "www.example.com")
        self.assertEqual(p[1], 8080)
        self.assertEqual(p[2], "/r?key=value")
        self.assertEqual(p[3], True)

        self.assertRaises(ValueError, ws._parse_url, "http://www.example.com/r")

    def testWSKey(self):
        key = ws._create_sec_websocket_key()
        self.assertTrue(key != 24)
        self.assertTrue("¥n" not in key)

    def testWsUtils(self):
        sock = ws.WebSocket()

        key = "c6b8hTg4EeGb2gQMztV1/g=="
        required_header = {
            "upgrade": "websocket",
            "connection": "upgrade",
            "sec-websocket-accept": "Kxep+hNu9n51529fGidYu7a3wO0=",
            }
        self.assertEqual(sock._validate_header(required_header, key), True)

        header = required_header.copy()
        header["upgrade"] = "http"
        self.assertEqual(sock._validate_header(header, key), False)
        del header["upgrade"]
        self.assertEqual(sock._validate_header(header, key), False)

        header = required_header.copy()
        header["connection"] = "something"
        self.assertEqual(sock._validate_header(header, key), False)
        del header["connection"]
        self.assertEqual(sock._validate_header(header, key), False)

        header = required_header.copy()
        header["sec-websocket-accept"] = "something"
        self.assertEqual(sock._validate_header(header, key), False)
        del header["sec-websocket-accept"]
        self.assertEqual(sock._validate_header(header, key), False)
        sock.close()

    def testReadHeader(self):
        sock = ws.WebSocket()
        sock.sock.close()
        sock.sock = HeaderSockMock("data/header01.txt")
        status, header = sock._read_headers()
        self.assertEqual(status, 101)
        self.assertEqual(header["connection"], "upgrade")

        sock.sock = HeaderSockMock("data/header02.txt")
        self.assertRaises(ws.WebSocketException, sock._read_headers)

    def testSend(self):
        # TODO: add longer frame data
        sock = ws.WebSocket()
        sock.set_mask_key(create_mask_key)
        sock.sock.close()
        s = sock.sock = HeaderSockMock("data/header01.txt")
        sock.send("Hello")
        self.assertEqual(s.sent[0], b"\x81\x85abcd)\x07\x0f\x08\x0e")

        sock.send("こんにちは")
        self.assertEqual(s.sent[1], b"\x81\x8fabcd\x82\xe3\xf0\x87\xe3\xf1\x80\xe5\xca\x81\xe2\xc5\x82\xe3\xcc")

        sock.send(u"こんにちは")
        self.assertEqual(s.sent[1], b"\x81\x8fabcd\x82\xe3\xf0\x87\xe3\xf1\x80\xe5\xca\x81\xe2\xc5\x82\xe3\xcc")

    def testRecv(self):
        # TODO: add longer frame data
        sock = ws.WebSocket()
        sock.sock.close()
        s = sock.sock = StringSockMock()
        s.set_data(b"\x81\x8fabcd\x82\xe3\xf0\x87\xe3\xf1\x80\xe5\xca\x81\xe2\xc5\x82\xe3\xcc")
        data = sock.recv()
        self.assertEqual(data, "こんにちは")

        s.set_data(b"\x81\x85abcd)\x07\x0f\x08\x0e")
        data = sock.recv()
        self.assertEqual(data, "Hello")

    def testWebSocket(self):
        s = ws.create_connection("ws://echo.websocket.org/")
        self.assertNotEqual(s, None)
        s.send("Hello, World")
        result = s.recv()
        self.assertEqual(result, "Hello, World")

        s.send("こにゃにゃちは、世界")
        result = s.recv()
        self.assertEqual(result, "こにゃにゃちは、世界")
        s.close()

    def testPingPong(self):
        s = ws.create_connection("ws://echo.websocket.org/")
        self.assertNotEqual(s, None)
        s.ping("Hello")
        s.pong("Hi")
        s.close()

    def testSecureWebSocket(self):
        s = ws.create_connection("wss://echo.websocket.org/")
        self.assertNotEqual(s, None)
        self.assertTrue(isinstance(s.sock, ws._SSLSocketWrapper))
        s.send("Hello, World")
        result = s.recv()
        self.assertEqual(result, "Hello, World")
        s.send("こにゃにゃちは、世界")
        result = s.recv()
        self.assertEqual(result, "こにゃにゃちは、世界")
        s.close()

    def testWebSocketWihtCustomHeader(self):
        s = ws.create_connection("ws://echo.websocket.org/",
                                  headers={"User-Agent": "PythonWebsocketClient"})
        self.assertNotEqual(s, None)
        s.send("Hello, World")
        result = s.recv()
        self.assertEqual(result, "Hello, World")
        s.close()

    def testAfterClose(self):
        from socket import error
        s = ws.create_connection("ws://echo.websocket.org/")
        self.assertNotEqual(s, None)
        s.close()
        self.assertRaises(error, s.send, "Hello")
        self.assertRaises(error, s.recv)

    def testUUID4(self):
        """ WebSocket key should be a UUID4.
        """
        key = ws._create_sec_websocket_key()
        u = uuid.UUID(bytes=base64.b64decode(key))
        self.assertEqual(4, u.version)


class WebSocketAppTest(unittest.TestCase):

    class NotSetYet(object):
        """ A marker class for signalling that a value hasn't been set yet.
        """

    def setUp(self):
        ws.enableTrace(TRACABLE)

        WebSocketAppTest.keep_running_open = WebSocketAppTest.NotSetYet()
        WebSocketAppTest.keep_running_close = WebSocketAppTest.NotSetYet()
        WebSocketAppTest.get_mask_key_id = WebSocketAppTest.NotSetYet()

    def tearDown(self):
        WebSocketAppTest.keep_running_open = WebSocketAppTest.NotSetYet()
        WebSocketAppTest.keep_running_close = WebSocketAppTest.NotSetYet()
        WebSocketAppTest.get_mask_key_id = WebSocketAppTest.NotSetYet()

    def testKeepRunning(self):
        """ A WebSocketApp should keep running as long as its self.keep_running
        is not False (in the boolean context).
        """

        def on_open(self, *args, **kwargs):
            """ Set the keep_running flag for later inspection and immediately
            close the connection.
            """
            WebSocketAppTest.keep_running_open = self.keep_running
            self.close()

        def on_close(self, *args, **kwargs):
            """ Set the keep_running flag for the test to use.
            """
            WebSocketAppTest.keep_running_close = self.keep_running

        app = ws.WebSocketApp('ws://echo.websocket.org/', on_open=on_open, on_close=on_close)
        app.run_forever()

        self.assertFalse(isinstance(WebSocketAppTest.keep_running_open,
                                    WebSocketAppTest.NotSetYet))

        self.assertFalse(isinstance(WebSocketAppTest.keep_running_close,
                                    WebSocketAppTest.NotSetYet))

        self.assertEqual(True, WebSocketAppTest.keep_running_open)
        self.assertEqual(False, WebSocketAppTest.keep_running_close)

    def testSockMaskKey(self):
        """ A WebSocketApp should forward the received mask_key function down
        to the actual socket.
        """

        def my_mask_key_func():
            pass

        def on_open(self, *args, **kwargs):
            """ Set the value so the test can use it later on and immediately
            close the connection.
            """
            WebSocketAppTest.get_mask_key_id = id(self.get_mask_key)
            self.close()

        app = ws.WebSocketApp('ws://echo.websocket.org/', on_open=on_open, get_mask_key=my_mask_key_func)
        app.run_forever()

        # Note: We can't use 'is' for comparing the functions directly, need to use 'id'.
        self.assertEqual(WebSocketAppTest.get_mask_key_id, id(my_mask_key_func))

if __name__ == "__main__":
    unittest.main()
