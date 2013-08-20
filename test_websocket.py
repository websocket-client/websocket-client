# -*- coding: utf-8 -*-
#

import base64
import socket
import ssl
import unittest
import uuid

# websocket-client
import websocket as ws

TRACABLE=False

def create_mask_key(n):
    return "abcd"

class SockMock(object):

    def __init__(self):
        self.data = []
        self.sent = []

    def add_packet(self, data):
        self.data.append(data)

    def recv(self, bufsize):
        if self.data:
            e = self.data.pop(0)
            if isinstance(e, Exception):
                raise e
            if len(e) > bufsize:
                self.data.insert(0, e[bufsize:])
            return e[:bufsize]

    def send(self, data):
        self.sent.append(data)
        return len(data)


class HeaderSockMock(SockMock):

    def __init__(self, fname):
        SockMock.__init__(self)
        self.add_packet(open(fname).read())


class WebSocketTest(unittest.TestCase):
    def setUp(self):
        ws.enableTrace(TRACABLE)
    
    def tearDown(self):
        pass

    def testDefaultTimeout(self):
        self.assertEquals(ws.getdefaulttimeout(), None)
        ws.setdefaulttimeout(10)
        self.assertEquals(ws.getdefaulttimeout(), 10)
        ws.setdefaulttimeout(None)

    def testParseUrl(self):
        p = ws._parse_url("ws://www.example.com/r")
        self.assertEquals(p[0], "www.example.com")
        self.assertEquals(p[1], 80)
        self.assertEquals(p[2], "/r")
        self.assertEquals(p[3], False)

        p = ws._parse_url("ws://www.example.com/r/")
        self.assertEquals(p[0], "www.example.com")
        self.assertEquals(p[1], 80)
        self.assertEquals(p[2], "/r/")
        self.assertEquals(p[3], False)

        p = ws._parse_url("ws://www.example.com/")
        self.assertEquals(p[0], "www.example.com")
        self.assertEquals(p[1], 80)
        self.assertEquals(p[2], "/")
        self.assertEquals(p[3], False)

        p = ws._parse_url("ws://www.example.com")
        self.assertEquals(p[0], "www.example.com")
        self.assertEquals(p[1], 80)
        self.assertEquals(p[2], "/")
        self.assertEquals(p[3], False)

        p = ws._parse_url("ws://www.example.com:8080/r")
        self.assertEquals(p[0], "www.example.com")
        self.assertEquals(p[1], 8080)
        self.assertEquals(p[2], "/r")
        self.assertEquals(p[3], False)

        p = ws._parse_url("ws://www.example.com:8080/")
        self.assertEquals(p[0], "www.example.com")
        self.assertEquals(p[1], 8080)
        self.assertEquals(p[2], "/")
        self.assertEquals(p[3], False)

        p = ws._parse_url("ws://www.example.com:8080")
        self.assertEquals(p[0], "www.example.com")
        self.assertEquals(p[1], 8080)
        self.assertEquals(p[2], "/")
        self.assertEquals(p[3], False)

        p = ws._parse_url("wss://www.example.com:8080/r")
        self.assertEquals(p[0], "www.example.com")
        self.assertEquals(p[1], 8080)
        self.assertEquals(p[2], "/r")
        self.assertEquals(p[3], True)

        p = ws._parse_url("wss://www.example.com:8080/r?key=value")
        self.assertEquals(p[0], "www.example.com")
        self.assertEquals(p[1], 8080)
        self.assertEquals(p[2], "/r?key=value")
        self.assertEquals(p[3], True)

        self.assertRaises(ValueError, ws._parse_url, "http://www.example.com/r")

    def testWSKey(self):
        key = ws._create_sec_websocket_key()
        self.assert_(key != 24)
        self.assert_("¥n" not in key)

    def testWsUtils(self):
        sock = ws.WebSocket()

        key = "c6b8hTg4EeGb2gQMztV1/g=="
        required_header = {
            "upgrade": "websocket",
            "connection": "upgrade",
            "sec-websocket-accept": "Kxep+hNu9n51529fGidYu7a3wO0=",
            }
        self.assertEquals(sock._validate_header(required_header, key), True)

        header = required_header.copy()
        header["upgrade"] = "http"
        self.assertEquals(sock._validate_header(header, key), False)
        del header["upgrade"]
        self.assertEquals(sock._validate_header(header, key), False)

        header = required_header.copy()
        header["connection"] = "something"
        self.assertEquals(sock._validate_header(header, key), False)
        del header["connection"]
        self.assertEquals(sock._validate_header(header, key), False)

        header = required_header.copy()
        header["sec-websocket-accept"] = "something"
        self.assertEquals(sock._validate_header(header, key), False)
        del header["sec-websocket-accept"]
        self.assertEquals(sock._validate_header(header, key), False)

    def testReadHeader(self):
        sock = ws.WebSocket()
        sock.sock = HeaderSockMock("data/header01.txt")
        status, header = sock._read_headers()
        self.assertEquals(status, 101)
        self.assertEquals(header["connection"], "upgrade")

        sock.sock = HeaderSockMock("data/header02.txt")
        self.assertRaises(ws.WebSocketException, sock._read_headers)

    def testSend(self):
        # TODO: add longer frame data
        sock = ws.WebSocket()
        sock.set_mask_key(create_mask_key)
        s = sock.sock = HeaderSockMock("data/header01.txt")
        sock.send("Hello")
        self.assertEquals(s.sent[0], "\x81\x85abcd)\x07\x0f\x08\x0e")

        sock.send("こんにちは")
        self.assertEquals(s.sent[1], "\x81\x8fabcd\x82\xe3\xf0\x87\xe3\xf1\x80\xe5\xca\x81\xe2\xc5\x82\xe3\xcc")

        sock.send(u"こんにちは")
        self.assertEquals(s.sent[1], "\x81\x8fabcd\x82\xe3\xf0\x87\xe3\xf1\x80\xe5\xca\x81\xe2\xc5\x82\xe3\xcc")

    def testRecv(self):
        # TODO: add longer frame data
        sock = ws.WebSocket()
        s = sock.sock = SockMock()
        s.add_packet("\x81\x8fabcd\x82\xe3\xf0\x87\xe3\xf1\x80\xe5\xca\x81\xe2\xc5\x82\xe3\xcc")
        data = sock.recv()
        self.assertEquals(data, "こんにちは")

        s.add_packet("\x81\x85abcd)\x07\x0f\x08\x0e")
        data = sock.recv()
        self.assertEquals(data, "Hello")

    def testInternalRecvStrict(self):
        sock = ws.WebSocket()
        s = sock.sock = SockMock()
        s.add_packet("foo")
        s.add_packet(socket.timeout())
        s.add_packet("bar")
        s.add_packet(ssl.SSLError("The read operation timed out"))
        s.add_packet("baz")
        with self.assertRaises(ws.WebSocketTimeoutException):
            data = sock._recv_strict(9)
        with self.assertRaises(ws.WebSocketTimeoutException):
            data = sock._recv_strict(9)
        data = sock._recv_strict(9)
        self.assertEquals(data, "foobarbaz")
        with self.assertRaises(ws.WebSocketConnectionClosedException):
            data = sock._recv_strict(1)

    def testRecvTimeout(self):
        sock = ws.WebSocket()
        s = sock.sock = SockMock()
        s.add_packet("\x81")
        s.add_packet(socket.timeout())
        s.add_packet("\x8dabcd\x29\x07\x0f\x08\x0e")
        s.add_packet(socket.timeout())
        s.add_packet("\x4e\x43\x33\x0e\x10\x0f\x00\x40")
        with self.assertRaises(ws.WebSocketTimeoutException):
            data = sock.recv()
        with self.assertRaises(ws.WebSocketTimeoutException):
            data = sock.recv()
        data = sock.recv()
        self.assertEquals(data, "Hello, World!")
        with self.assertRaises(ws.WebSocketConnectionClosedException):
            data = sock.recv()

    def testWebSocket(self):
        s = ws.create_connection("ws://echo.websocket.org/")
        self.assertNotEquals(s, None)
        s.send("Hello, World")
        result = s.recv()
        self.assertEquals(result, "Hello, World")

        s.send("こにゃにゃちは、世界")
        result = s.recv()
        self.assertEquals(result, "こにゃにゃちは、世界")
        s.close()

    def testPingPong(self):
        s = ws.create_connection("ws://echo.websocket.org/")
        self.assertNotEquals(s, None)
        s.ping("Hello")
        s.pong("Hi")
        s.close()

    def testSecureWebSocket(self):
        try:
            import ssl
            s = ws.create_connection("wss://echo.websocket.org/")
            self.assertNotEquals(s, None)
            self.assert_(isinstance(s.sock, ssl.SSLSock))
            s.send("Hello, World")
            result = s.recv()
            self.assertEquals(result, "Hello, World")
            s.send("こにゃにゃちは、世界")
            result = s.recv()
            self.assertEquals(result, "こにゃにゃちは、世界")
            s.close()
        except:
            pass

    def testWebSocketWihtCustomHeader(self):
        s = ws.create_connection("ws://echo.websocket.org/",
                                 headers={"User-Agent": "PythonWebsocketClient"})
        self.assertNotEquals(s, None)
        s.send("Hello, World")
        result = s.recv()
        self.assertEquals(result, "Hello, World")
        s.close()

    def testAfterClose(self):
        from socket import error
        s = ws.create_connection("ws://echo.websocket.org/")
        self.assertNotEquals(s, None)
        s.close()
        self.assertRaises(error, s.send, "Hello")
        self.assertRaises(error, s.recv)

    def testUUID4(self):
        """ WebSocket key should be a UUID4.
        """
        key = ws._create_sec_websocket_key()
        u = uuid.UUID(bytes=base64.b64decode(key))
        self.assertEquals(4, u.version)


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

        self.assertEquals(True, WebSocketAppTest.keep_running_open)
        self.assertEquals(False, WebSocketAppTest.keep_running_close)

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
        self.assertEquals(WebSocketAppTest.get_mask_key_id, id(my_mask_key_func))


class SockOptTest(unittest.TestCase):
    def testSockOpt(self):
        sockopt = ((socket.IPPROTO_TCP, socket.TCP_NODELAY, 1),)
        s = ws.WebSocket(sockopt=sockopt)
        self.assertNotEquals(s.sock.getsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY), 0)
        s = ws.create_connection("ws://echo.websocket.org", sockopt=sockopt)
        self.assertNotEquals(s.sock.getsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY), 0)


if __name__ == "__main__":
    unittest.main()
