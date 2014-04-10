# -*- coding: utf-8 -*-
#

import sys
sys.path[0:0] = [""]

import os.path
import base64
import socket
try:
    from ssl import SSLError
except ImportError:
    # dummy class of SSLError for ssl none-support environment.
    class SSLError(Exception):
        pass
import unittest
import uuid

# websocket-client
import websocket as ws

# There are three tests to test the library's behaviour when the received
# message is fragmented (please see [1] for details). They fail currently as
# the library doesn't yet support fragmentation. Therefore the tests are
# skipped unless the flag below is set.
#
# [1]: https://tools.ietf.org/html/rfc6455#section-5.4
#      "RFC6455: 5.4. Fragmentation"
#
TEST_FRAGMENTATION = True
TEST_WITH_INTERNET = False

TRACABLE = False


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
        path = os.path.join(os.path.dirname(__file__), fname)
        self.add_packet(open(path).read())


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

        p = ws._parse_url("ws://[2a03:4000:123:83::3]/r")
        self.assertEquals(p[0], "2a03:4000:123:83::3")
        self.assertEquals(p[1], 80)
        self.assertEquals(p[2], "/r")
        self.assertEquals(p[3], False)

        p = ws._parse_url("ws://[2a03:4000:123:83::3]:8080/r")
        self.assertEquals(p[0], "2a03:4000:123:83::3")
        self.assertEquals(p[1], 8080)
        self.assertEquals(p[2], "/r")
        self.assertEquals(p[3], False)

        p = ws._parse_url("wss://[2a03:4000:123:83::3]/r")
        self.assertEquals(p[0], "2a03:4000:123:83::3")
        self.assertEquals(p[1], 443)
        self.assertEquals(p[2], "/r")
        self.assertEquals(p[3], True)

        p = ws._parse_url("wss://[2a03:4000:123:83::3]:8080/r")
        self.assertEquals(p[0], "2a03:4000:123:83::3")
        self.assertEquals(p[1], 8080)
        self.assertEquals(p[2], "/r")
        self.assertEquals(p[3], True)

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
        s.add_packet(SSLError("The read operation timed out"))
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

    @unittest.skipUnless(TEST_FRAGMENTATION, "fragmentation not implemented")
    def testRecvWithSimpleFragmentation(self):
        sock = ws.WebSocket()
        s = sock.sock = SockMock()
        # OPCODE=TEXT, FIN=0, MSG="Brevity is "
        s.add_packet("\x01\x8babcd#\x10\x06\x12\x08\x16\x1aD\x08\x11C")
        # OPCODE=CONT, FIN=1, MSG="the soul of wit"
        s.add_packet("\x80\x8fabcd\x15\n\x06D\x12\r\x16\x08A\r\x05D\x16\x0b\x17")
        data = sock.recv()
        self.assertEqual(data, "Brevity is the soul of wit")
        with self.assertRaises(ws.WebSocketConnectionClosedException):
            sock.recv()

    @unittest.skipUnless(TEST_FRAGMENTATION, "fragmentation not implemented")
    def testRecvContFragmentation(self):
        sock = ws.WebSocket()
        s = sock.sock = SockMock()
        # OPCODE=CONT, FIN=1, MSG="the soul of wit"
        s.add_packet("\x80\x8fabcd\x15\n\x06D\x12\r\x16\x08A\r\x05D\x16\x0b\x17")
        self.assertRaises(ws.WebSocketException, sock.recv)

    @unittest.skipUnless(TEST_FRAGMENTATION, "fragmentation not implemented")
    def testRecvWithProlongedFragmentation(self):
        sock = ws.WebSocket()
        s = sock.sock = SockMock()
        # OPCODE=TEXT, FIN=0, MSG="Once more unto the breach, "
        s.add_packet("\x01\x9babcd.\x0c\x00\x01A\x0f\x0c\x16\x04B\x16\n\x15" \
                     "\rC\x10\t\x07C\x06\x13\x07\x02\x07\tNC")
        # OPCODE=CONT, FIN=0, MSG="dear friends, "
        s.add_packet("\x00\x8eabcd\x05\x07\x02\x16A\x04\x11\r\x04\x0c\x07" \
                     "\x17MB")
        # OPCODE=CONT, FIN=1, MSG="once more"
        s.add_packet("\x80\x89abcd\x0e\x0c\x00\x01A\x0f\x0c\x16\x04")
        data = sock.recv()
        self.assertEqual(data, "Once more unto the breach, dear friends, " \
                               "once more")
        with self.assertRaises(ws.WebSocketConnectionClosedException):
            sock.recv()

    @unittest.skipUnless(TEST_FRAGMENTATION, "fragmentation not implemented")
    def testRecvWithFragmentationAndControlFrame(self):
        sock = ws.WebSocket()
        sock.set_mask_key(create_mask_key)
        s = sock.sock = SockMock()
        # OPCODE=TEXT, FIN=0, MSG="Too much "
        s.add_packet("\x01\x89abcd5\r\x0cD\x0c\x17\x00\x0cA")
        # OPCODE=PING, FIN=1, MSG="Please PONG this"
        s.add_packet("\x89\x90abcd1\x0e\x06\x05\x12\x07C4.,$D\x15\n\n\x17")
        # OPCODE=CONT, FIN=1, MSG="of a good thing"
        s.add_packet("\x80\x8fabcd\x0e\x04C\x05A\x05\x0c\x0b\x05B\x17\x0c" \
                     "\x08\x0c\x04")
        data = sock.recv()
        self.assertEqual(data, "Too much of a good thing")
        with self.assertRaises(ws.WebSocketConnectionClosedException):
            sock.recv()
        self.assertEqual(s.sent[0], "\x8a\x90abcd1\x0e\x06\x05\x12\x07C4.,$D" \
                                    "\x15\n\n\x17")

    @unittest.skipUnless(TEST_WITH_INTERNET, "Internet-requiring tests are disabled")
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

    @unittest.skipUnless(TEST_WITH_INTERNET, "Internet-requiring tests are disabled")
    def testPingPong(self):
        s = ws.create_connection("ws://echo.websocket.org/")
        self.assertNotEquals(s, None)
        s.ping("Hello")
        s.pong("Hi")
        s.close()

    @unittest.skipUnless(TEST_WITH_INTERNET, "Internet-requiring tests are disabled")
    def testSecureWebSocket(self):
        if 1:
            import ssl
            s = ws.create_connection("wss://echo.websocket.org/")
            self.assertNotEquals(s, None)
            self.assert_(isinstance(s.sock, ssl.SSLSocket))
            s.send("Hello, World")
            result = s.recv()
            self.assertEquals(result, "Hello, World")
            s.send("こにゃにゃちは、世界")
            result = s.recv()
            self.assertEquals(result, "こにゃにゃちは、世界")
            s.close()
        #except:
        #    pass

    @unittest.skipUnless(TEST_WITH_INTERNET, "Internet-requiring tests are disabled")
    def testWebSocketWihtCustomHeader(self):
        s = ws.create_connection("ws://echo.websocket.org/",
                                 headers={"User-Agent": "PythonWebsocketClient"})
        self.assertNotEquals(s, None)
        s.send("Hello, World")
        result = s.recv()
        self.assertEquals(result, "Hello, World")
        s.close()

    @unittest.skipUnless(TEST_WITH_INTERNET, "Internet-requiring tests are disabled")
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

    @unittest.skipUnless(TEST_WITH_INTERNET, "Internet-requiring tests are disabled")
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

    @unittest.skipUnless(TEST_WITH_INTERNET, "Internet-requiring tests are disabled")
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
    @unittest.skipUnless(TEST_WITH_INTERNET, "Internet-requiring tests are disabled")
    def testSockOpt(self):
        sockopt = ((socket.IPPROTO_TCP, socket.TCP_NODELAY, 1),)
        s = ws.WebSocket(sockopt=sockopt)
        self.assertNotEquals(s.sock.getsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY), 0)
        s = ws.create_connection("ws://echo.websocket.org", sockopt=sockopt)
        self.assertNotEquals(s.sock.getsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY), 0)


if __name__ == "__main__":
    unittest.main()
