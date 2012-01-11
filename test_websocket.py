# -*- coding: utf-8 -*-
#

import unittest
import websocket as ws

TRACABLE=False

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


class HeaderSockMock(StringSockMock):
    def __init__(self, fname):
        self.set_data(open(fname).read())
        self.sent = []


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
        sock.io_sock = sock.sock = HeaderSockMock("data/header01.txt")
        status, header = sock._read_headers()
        self.assertEquals(status, 101)
        self.assertEquals(header["connection"], "upgrade")
        
        sock.io_sock = sock.sock = HeaderSockMock("data/header02.txt")
        self.assertRaises(ws.WebSocketException, sock._read_headers)

    def testSend(self):
        sock = ws.WebSocket()
        s = sock.io_sock = sock.sock = HeaderSockMock("data/header01.txt")
        sock.send("Hello")
        #self.assertEquals(s.sent[0], "\x00Hello\xff")
        sock.send("こんにちは")
        #self.assertEquals(s.sent[1], "\x00こんにちは\xff")
        sock.send(u"こんにちは")
        #self.assertEquals(s.sent[1], "\x00こんにちは\xff")

    def testRecv(self):
        sock = ws.WebSocket()
        s = sock.io_sock = sock.sock = StringSockMock()
        s.set_data("\x00こんにちは\xff")
        data = sock.recv()
        self.assertEquals(data, "こんにちは")
        
        s.set_data("\x81\x05Hello")
        data = sock.recv()
        self.assertEquals(data, "Hello")

        s.set_data("\x81\x81\x7f" + ("a"*255))
        data = sock.recv()
        self.assertEquals(len(data), 255)
        self.assertEquals(data, "a" * 255)

    def testWebSocket(self):
        s  = ws.create_connection("ws://echo.websocket.org/") #ws://localhost:8080/echo")
        self.assertNotEquals(s, None)
        s.send("Hello, World")
        result = s.recv()
        self.assertEquals(result, "Hello, World")
        s.send("こにゃにゃちは、世界")
        result = s.recv()
        self.assertEquals(result, "こにゃにゃちは、世界")
        s.close()

    def testSecureWebsocket(self):
        s  = ws.create_connection("wss://echo.websocket.org/")
        self.assertNotEquals(s, None)
        self.assert_(isinstance(s.io_sock, ws._SSLSocketWrapper))
        s.send("Hello, World")
        result = s.recv()
        self.assertEquals(result, "Hello, World")
        s.send("こにゃにゃちは、世界")
        result = s.recv()
        self.assertEquals(result, "こにゃにゃちは、世界")
        s.close()

    def testWebSocketWihtCustomHeader(self):
        s  = ws.create_connection("ws://echo.websocket.org/",
                                  headers={"User-Agent": "PythonWebsocketClient"})
        self.assertNotEquals(s, None)
        s.send("Hello, World")
        result = s.recv()
        self.assertEquals(result, "Hello, World")
        s.close()

    def testAfterClose(self):
        from socket import error
        s  = ws.create_connection("ws://echo.websocket.org/")
        self.assertNotEquals(s, None)
        s.close()
        self.assertRaises(error, s.send, "Hello")
        self.assertRaises(error, s.recv)
        
        

if __name__ == "__main__":
    unittest.main()

