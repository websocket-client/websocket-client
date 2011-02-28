"""
websocket - WebSocket client library for Python

Copyright (C) 2010 Hiroki Ohtani(liris)

    This library is free software; you can redistribute it and/or
    modify it under the terms of the GNU Lesser General Public
    License as published by the Free Software Foundation; either
    version 2.1 of the License, or (at your option) any later version.

    This library is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
    Lesser General Public License for more details.

    You should have received a copy of the GNU Lesser General Public
    License along with this library; if not, write to the Free Software
    Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA

"""        


import socket
from urlparse import urlparse
import random
import struct
import md5
import logging


logger = logging.getLogger()

class WebSocketException(Exception):
    pass

class ConnectionClosedException(WebSocketException):
    pass

default_timeout = None
traceEnabled = False

def enableTrace(tracable):
    """
    turn on/off the tracability.
    """
    global traceEnabled
    traceEnabled = tracable
    if tracable:
        if not logger.handlers:
            logger.addHandler(logging.StreamHandler())
        logger.setLevel(logging.DEBUG)

def setdefaulttimeout(timeout):
    """
    Set the global timeout setting to connect.
    """
    global default_timeout
    default_timeout = timeout


def getdefaulttimeout():
    """
    Return the global timeout setting to connect.
    """
    return default_timeout

def _parse_url(url):
    """
    parse url and the result is tuple of 
    (hostname, port, resource path and the flag of secure mode)
    """
    parsed = urlparse(url)
    if parsed.hostname:
        hostname = parsed.hostname
    else:
        raise ValueError("hostname is invalid")
    port = 0
    if parsed.port:
        port = parsed.port
   
    is_secure = False
    if parsed.scheme == "ws":
        if not port:
            port = 80
    elif parsed.scheme == "wss":
        is_secure = True
        if not port:
            port  = 443
    else:
        raise ValueError("scheme %s is invalid" % parsed.scheme)
    
    if parsed.path:
        resource = parsed.path
    else:
        resource = "/"
    
    return (hostname, port, resource, is_secure)


def create_connection(url, timeout=None, **options):
    """
    connect to url and return websocket object.

    Connect to url and return the WebSocket object.
    Passing optional timeout parameter will set the timeout on the socket.
    If no timeout is supplied, the global default timeout setting returned by getdefauttimeout() is used.
    """
    websock = WebSocket()
    websock.settimeout(timeout != None and timeout or default_timeout)
    websock.connect(url, **options)
    return websock

_MAX_INTEGER = (1 << 32) -1
_AVAILABLE_KEY_CHARS = range(0x21, 0x2f + 1) + range(0x3a, 0x7e + 1)
_MAX_CHAR_BYTE = (1<<8) -1

# ref. Websocket gets an update, and it breaks stuff.
# http://axod.blogspot.com/2010/06/websocket-gets-update-and-it-breaks.html

def _create_sec_websocket_key():
    spaces_n = random.randint(1, 12)
    max_n = _MAX_INTEGER / spaces_n
    number_n = random.randint(0, max_n)
    product_n = number_n * spaces_n
    key_n = str(product_n)
    for i in range(random.randint(1, 12)):
        c = random.choice(_AVAILABLE_KEY_CHARS)
        pos = random.randint(0, len(key_n))
        key_n = key_n[0:pos] + chr(c) + key_n[pos:]
    for i in range(spaces_n):
        pos = random.randint(1, len(key_n)-1)
        key_n = key_n[0:pos] + " " + key_n[pos:]
    
    return number_n, key_n

def _create_key3():
    return "".join([chr(random.randint(0, _MAX_CHAR_BYTE)) for i in range(8)])

HEADERS_TO_CHECK = {
    "upgrade": "websocket",
    "connection": "upgrade",
    }

HEADERS_TO_EXIST_FOR_HYBI00 = [
    "sec-websocket-origin",
    "sec-websocket-location",
]

HEADERS_TO_EXIST_FOR_HIXIE75 = [
    "websocket-origin",
    "websocket-location",
]

class _SSLSocketWrapper(object):
    def __init__(self, sock):
        self.ssl = socket.ssl(sock)

    def recv(self, bufsize):
        return self.ssl.read(bufsize)
    
    def send(self, payload):
        return self.ssl.write(payload)

class WebSocket(object):
    """
    Low level WebSocket interface.
    This class is based on
      The WebSocket protocol draft-hixie-thewebsocketprotocol-76
      http://tools.ietf.org/html/draft-hixie-thewebsocketprotocol-76

    We can connect to the websocket server and send/recieve data.
    The following example is a echo client.

    >>> import websocket
    >>> ws = websocket.WebSocket()
    >>> ws.Connect("ws://localhost:8080/echo")
    >>> ws.send("Hello, Server")
    >>> ws.recv()
    'Hello, Server'
    >>> ws.close()
    """
    def __init__(self):
        """
        Initalize WebSocket object.
        """
        self.connected = False
        self.io_sock = self.sock = socket.socket()

    def settimeout(self, timeout):
        """
        Set the timeout to the websocket.
        """
        self.sock.settimeout(timeout)

    def gettimeout(self):
        """
        Get the websocket timeout.
        """
        return self.sock.gettimeout()
    
    def connect(self, url, **options):
        """
        Connect to url. url is websocket url scheme. ie. ws://host:port/resource
        """
        hostname, port, resource, is_secure = _parse_url(url)
        # TODO: we need to support proxy
        self.sock.connect((hostname, port))
        if is_secure:
            self.io_sock = _SSLSocketWrapper(self.sock)
        self._handshake(hostname, port, resource, **options)

    def _handshake(self, host, port, resource, **options):
        sock = self.io_sock
        headers = []
        headers.append("GET %s HTTP/1.1" % resource)
        headers.append("Upgrade: WebSocket")
        headers.append("Connection: Upgrade")
        if port == 80:
            hostport = host
        else:
            hostport = "%s:%d" % (host, port)
        headers.append("Host: %s" % hostport)
        headers.append("Origin: %s" % hostport)
   
        number_1, key_1 = _create_sec_websocket_key()
        headers.append("Sec-WebSocket-Key1: %s" % key_1)
        number_2, key_2 = _create_sec_websocket_key()
        headers.append("Sec-WebSocket-Key2: %s" % key_2)
        if "header" in options:
            headers.extend(options["header"])

        headers.append("")
        key3 = _create_key3()
        headers.append(key3)

        header_str = "\r\n".join(headers)
        sock.send(header_str)
        if traceEnabled:
            logger.debug( "--- request header ---")
            logger.debug( header_str)
            logger.debug("-----------------------")

        status, resp_headers = self._read_headers()
        if status != 101:
            self.close()
            raise WebSocketException("Handshake Status %d" % status)
        success, secure = self._validate_header(resp_headers)
        if not success:
            self.close()
            raise WebSocketException("Invalid WebSocket Header")
        
        if secure:
            resp = self._get_resp()
            if not self._validate_resp(number_1, number_2, key3, resp):
                self.close()
                raise WebSocketException("challenge-response error")

        self.connected = True
    
    def _validate_resp(self, number_1, number_2, key3, resp):
        challenge = struct.pack("!I", number_1)
        challenge += struct.pack("!I", number_2)
        challenge += key3
        digest = md5.md5(challenge).digest()
        
        return  resp == digest

    def _get_resp(self):
        result = self._recv(16)
        if traceEnabled:
            logger.debug("--- challenge response result ---")
            logger.debug(repr(result))
            logger.debug("---------------------------------")
        
        return result

    def _validate_header(self, headers):
        #TODO: check other headers
        for key, value in HEADERS_TO_CHECK.iteritems():
            v = headers.get(key, None)
            if value != v:
                return False, False

        success = 0
        for key in HEADERS_TO_EXIST_FOR_HYBI00:
            if key in headers:
                success += 1
        if success == len(HEADERS_TO_EXIST_FOR_HYBI00):
            return True, True
        elif success != 0:
            return False, True

        success = 0
        for key in HEADERS_TO_EXIST_FOR_HIXIE75:
            if key in headers:
                success += 1
        if success == len(HEADERS_TO_EXIST_FOR_HIXIE75):
            return True, False

        return False, False
            

    def _read_headers(self):
        status = None
        headers = {}
        if traceEnabled:
            logger.debug("--- response header ---")
            
        while True:
            line = self._recv_line()
            if line == "\r\n":
                break
            line = line.strip()
            if traceEnabled:
                logger.debug(line)
            if not status:
                status_info = line.split(" ", 2)
                status = int(status_info[1])
            else:
                kv = line.split(":", 1)
                if len(kv) == 2:
                    key, value = kv
                    headers[key.lower()] = value.strip().lower()
                else:
                    raise WebSocketException("Invalid header")

        if traceEnabled:
            logger.debug("-----------------------")
        
        return status, headers    
    
    def send(self, payload):
        """
        Send the data as string. payload must be utf-8 string or unicoce.
        """
        if isinstance(payload, unicode):
            payload = payload.encode("utf-8")
        data = "".join(["\x00", payload, "\xff"])
        self.io_sock.send(data)
        if traceEnabled:
            logger.debug("send: " + repr(data))

    def recv(self):
        """
        Reeive utf-8 string data from the server.
        """
        b = self._recv(1)
        if enableTrace:
            logger.debug("recv frame: " + repr(b))
        frame_type = ord(b)
        if frame_type == 0x00:
            bytes = []
            while True:
                b = self._recv(1)
                if b == "\xff":
                    break
                else:
                    bytes.append(b)
            return "".join(bytes)
        elif 0x80 < frame_type < 0xff:
            # which frame type is valid?
            length = self._read_length()
            bytes = self._recv_strict(length)
            return bytes
        elif frame_type == 0xff:
            n = self._recv(1)
            self._closeInternal()
            return None
        else:
            raise WebSocketException("Invalid frame type")

    def _read_length(self):
        length = 0
        while True:
            b = ord(self._recv(1))
            length = length * (1 << 7) + (b & 0x7f)
            if b < 0x80:
                break
            
        return length

    def close(self):
        """
        Close Websocket object
        """
        if self.connected:
            try:
                self.io_sock.send("\xff\x00")
                timeout = self.sock.gettimeout()
                self.sock.settimeout(1)
                try:
                    result = self._recv(2)
                    if result != "\xff\x00":
                        logger.error("bad closing Handshake")
                except:
                    pass
                self.sock.settimeout(timeout)
                self.sock.shutdown(socket.SHUT_RDWR)
            except:
                pass
        self._closeInternal()

    def _closeInternal(self):
        self.connected = False
        self.sock.close()
        self.io_sock = self.sock
        
    def _recv(self, bufsize):
        bytes = self.io_sock.recv(bufsize)
        if not bytes:
            raise ConnectionClosedException()
        return bytes

    def _recv_strict(self, bufsize):
        remaining = bufsize
        bytes = ""
        while remaining:
            bytes += self._recv(remaining)
            remaining = bufsize - len(bytes)
            
        return bytes

    def _recv_line(self):
        line = []
        while True:
            c = self._recv(1)
            line.append(c)
            if c == "\n":
                break
        return "".join(line)
            
class WebSocketApp(object):
    """
    Higher level of APIs are provided. 
    The interface is like JavaScript WebSocket object.
    """
    def __init__(self, url,
                 on_open = None, on_message = None, on_error = None, 
                 on_close = None):
        """
        url: websocket url.
        on_open: callable object which is called at opening websocket.
          this function has one argument. The arugment is this class object.
        on_message: callbale object which is called when recieved data.
         on_message has 2 arguments. 
         The 1st arugment is this class object.
         The passing 2nd arugment is utf-8 string which we get from the server.
       on_error: callable object which is called when we get error.
         on_error has 2 arguments.
         The 1st arugment is this class object.
         The passing 2nd arugment is exception object.
       on_close: callable object which is called when closed the connection.
         this function has one argument. The arugment is this class object.
        """
        self.url = url
        self.on_open = on_open
        self.on_message = on_message
        self.on_error = on_error
        self.on_close = on_close
        self.sock = None

    def send(self, data):
        """
        send message. data must be utf-8 string or unicode.
        """
        self.sock.send(data)

    def close(self):
        """
        close websocket connection.
        """
        self.sock.close()

    def run_forever(self):
        """
        run event loop for WebSocket framework.
        This loop is infinite loop and is alive during websocket is available.
        """
        if self.sock:
            raise WebSocketException("socket is already opened")
        try:
            self.sock = WebSocket()
            self.sock.connect(self.url)
            self._run_with_no_err(self.on_open)
            while True:
                data = self.sock.recv()
                if data is None:
                    break
                self._run_with_no_err(self.on_message, data)
        except Exception, e:
            self._run_with_no_err(self.on_error, e)
        finally:
            self.sock.close()
            self._run_with_no_err(self.on_close)
            self.sock = None

    def _run_with_no_err(self, callback, *args):
        if callback:
            try:
                callback(self, *args)
            except Exception, e:
                if logger.isEnabledFor(logging.DEBUG):
                    logger.error(e)


if __name__ == "__main__":
    enableTrace(True)
    #ws = create_connection("ws://localhost:8080/echo")
    ws = create_connection("ws://localhost:5000/chat")
    print "Sending 'Hello, World'..."
    ws.send("Hello, World")
    print "Sent"
    print "Receiving..."
    result =  ws.recv()
    print "Received '%s'" % result
    ws.close()
        




