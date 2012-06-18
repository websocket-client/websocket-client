# -*- coding: utf-8 -*-
#

import base64
import uuid
import unittest

# websocket-client
import websocket as ws

TRACABLE=False

def create_mask_key(n):
    return "abcd"

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
        sock.io_sock = sock.sock = HeaderSockMock("data/header01.txt")
        status, header = sock._read_headers()
        self.assertEquals(status, 101)
        self.assertEquals(header["connection"], "upgrade")
        
        sock.io_sock = sock.sock = HeaderSockMock("data/header02.txt")
        self.assertRaises(ws.WebSocketException, sock._read_headers)

    def testSend(self):
        # TODO: add longer frame data
        sock = ws.WebSocket()
        sock.set_mask_key(create_mask_key)
        s = sock.io_sock = sock.sock = HeaderSockMock("data/header01.txt")
        sock.send("Hello")
        self.assertEquals(s.sent[0], "\x81\x85abcd)\x07\x0f\x08\x0e")

        sock.send("こんにちは")
        self.assertEquals(s.sent[1], "\x81\x8fabcd\x82\xe3\xf0\x87\xe3\xf1\x80\xe5\xca\x81\xe2\xc5\x82\xe3\xcc")

        sock.send(u"こんにちは")
        self.assertEquals(s.sent[1], "\x81\x8fabcd\x82\xe3\xf0\x87\xe3\xf1\x80\xe5\xca\x81\xe2\xc5\x82\xe3\xcc")

    def testRecv(self):
        # TODO: add longer frame data
        sock = ws.WebSocket()
        s = sock.io_sock = sock.sock = StringSockMock()
        s.set_data("\x81\x8fabcd\x82\xe3\xf0\x87\xe3\xf1\x80\xe5\xca\x81\xe2\xc5\x82\xe3\xcc")
        data = sock.recv()
        self.assertEquals(data, "こんにちは")
        
        s.set_data("\x81\x85abcd)\x07\x0f\x08\x0e")
        data = sock.recv()
        self.assertEquals(data, "Hello")

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

    def testPingPong(self):
        s  = ws.create_connection("ws://echo.websocket.org/")
        self.assertNotEquals(s, None)
        s.ping("Hello")
        s.pong("Hi")
        s.close()
        
    def testSecureWebSocket(self):
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
        

if __name__ == "__main__":
    unittest.main()

