# -*- coding: utf-8 -*-
#

import unittest
import websocket as ws

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
        ws.enableTrace(True)
    
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
        n, k = ws._create_sec_websocket_key()
        self.assert_(0 < n < (1<<32))
        self.assert_(len(k) > 0)

        k3 = ws._create_key3()
        self.assertEquals(len(k3), 8)

    def testWsUtils(self):
        sock = ws.WebSocket()
        self.assertNotEquals(sock._validate_resp(1,2,"test", "fuga"), True)
        hashed = '6\xa3p\xb6#\xac\xb9=\xec\x0e\x96\xb5\xc1@\x1d\x90'
        self.assertEquals(sock._validate_resp(1,2,"test", hashed), True)

        hibi_header = {
            "upgrade": "websocket",
            "connection": "upgrade",
            "sec-websocket-origin": "http://www.example.com",
            "sec-websocket-location": "http://www.example.com",
            }
        self.assertEquals(sock._validate_header(hibi_header), (True, True))

        header = hibi_header.copy()
        header["upgrade"] = "http"
        self.assertEquals(sock._validate_header(header), (False, False))
        del header["upgrade"]
        self.assertEquals(sock._validate_header(header), (False, False))
        
        header = hibi_header.copy()
        header["connection"] = "http"
        self.assertEquals(sock._validate_header(header), (False, False))
        del header["connection"]
        self.assertEquals(sock._validate_header(header), (False, False))

        header = hibi_header.copy()
        header["sec-websocket-origin"] = "somewhere origin"
        self.assertEquals(sock._validate_header(header), (True, True))
        del header["sec-websocket-origin"]
        self.assertEquals(sock._validate_header(header), (False, True))

        header = hibi_header.copy()
        header["sec-websocket-location"] = "somewhere location"
        self.assertEquals(sock._validate_header(header), (True, True))
        del header["sec-websocket-location"]
        self.assertEquals(sock._validate_header(header), (False, True))

    def testReadHeader(self):
        sock = ws.WebSocket()
        sock.io_sock = sock.sock = HeaderSockMock("data/header01.txt")
        status, header = sock._read_headers()
        self.assertEquals(status, 101)
        self.assertEquals(header["connection"], "upgrade")
        self.assertEquals("ssssss" in header, False)
        
        self.assertEquals(sock._get_resp(), "ssssss\r\naaaaaaaa")

        sock.io_sock = sock.sock = HeaderSockMock("data/header02.txt")
        self.assertRaises(ws.WebSocketException, sock._read_headers)

    def testSend(self):
        sock = ws.WebSocket()
        s = sock.io_sock = sock.sock = HeaderSockMock("data/header01.txt")
        sock.send("Hello")
        self.assertEquals(s.sent[0], "\x00Hello\xff")
        sock.send("こんにちは")
        self.assertEquals(s.sent[1], "\x00こんにちは\xff")
        sock.send(u"こんにちは")
        self.assertEquals(s.sent[1], "\x00こんにちは\xff")

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

if __name__ == "__main__":
    unittest.main()

