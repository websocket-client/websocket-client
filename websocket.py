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
import struct
import uuid
import sha
import base64
import logging


VERSION = 13

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
    if ":" not in url:
        raise ValueError("url is invalid")

    scheme, url = url.split(":", 1)
    url = url.rstrip("/")

    parsed = urlparse(url, scheme="http")
    if parsed.hostname:
        hostname = parsed.hostname
    else:
        raise ValueError("hostname is invalid")
    port = 0
    if parsed.port:
        port = parsed.port

    is_secure = False
    if scheme == "ws":
        if not port:
            port = 80
    elif scheme == "wss":
        is_secure = True
        if not port:
            port  = 443
    else:
        raise ValueError("scheme %s is invalid" % scheme)

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
    You can customize using 'options'.
    If you set "headers" dict object, you can set your own custom header.

    >>> conn = create_connection("ws://echo.websocket.org/",
    ...     headers={"User-Agent": "MyProgram"})
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
    uid = uuid.uuid1()
    return base64.encodestring(uid.bytes).strip()

HEADERS_TO_CHECK = {
    "upgrade": "websocket",
    "connection": "upgrade",
    }

class _SSLSocketWrapper(object):
    def __init__(self, sock):
        self.ssl = socket.ssl(sock)

    def recv(self, bufsize):
        return self.ssl.read(bufsize)
    
    def send(self, payload):
        return self.ssl.write(payload)

BOOL_VALUES = (0, 1)
def is_bool(*values):
    for v in values:
        if v not in BOOL_VALUES:
            return False
    
    return True

class ABNF(object):
    """
    ABNF frame class.
    see http://tools.ietf.org/html/rfc5234
    and http://tools.ietf.org/html/rfc6455#section-5.2
    """
    OPCODE_TEXT   = 0x1
    OPCODE_BINARY = 0x2
    OPCODE_CLOSE  = 0x8
    OPCODE_PING   = 0x9
    OPCODE_PONG   = 0xa
    OPTCODES = (OPCODE_TEXT, OPCODE_BINARY, OPCODE_CLOSE,
                OPCODE_PING, OPCODE_PONG)

    LENGTH_7  = 0x7d
    LENGTH_16 = 1 << 16
    LENGTH_63 = 1 << 63

    def __init__(self, fin = 0, rsv1 = 0, rsv2 = 0, rsv3 = 0,
                 opcode = OPCODE_TEXT, mask = 0, data = ""):
        self.fin = fin
        self.rsv1 = rsv1
        self.rsv2 = rsv2
        self.rsv3 = rsv3
        self.opcode = opcode
        self.mask = mask
        self.data = data

    @staticmethod
    def create_frame(data, opcode):
        if opcode == ABNF.OPCODE_TEXT and isinstance(data, unicode):
            data = data.encode("utf-8")
        return ABNF(1, 0, 0, 0, opcode, 0, data)

    def format(self):
        if not is_bool(self.fin, self.rsv1, self.rsv2, self.rsv3):
            raise ValueError("not 0 or 1")
        if self.opcode not in ABNF.OPTCODES:
            raise ValueError("Invalid OPCODE")
        length = len(self.data)
        if length >= ABNF.LENGTH_63:
            raise ValueError("data is too long")
        
        frame_header = chr(self.fin << 7
                           | self.rsv1 << 6 | self.rsv2 << 5 | self.rsv3 << 4
                           | self.opcode)
        if length < ABNF.LENGTH_7:
            frame_header += chr(self.mask << 7 | length)
        elif length <= ABNF.LENGTH_16:
            frame_header += chr(self.mask << 7 | 0x7e)
            frame_header += struct.pack("!H", length)
        else:
            frame_header += chr(self.mask << 7 | 0x7f)
            frame_header += struct.pack("!Q", length)
        
        if not self.mask:
            return frame_header + self.data
        
        raise NotImplementedError("masked format is not implemented")
        
        

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
    >>> ws.connect("ws://echo.websocket.org")
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
        You can customize using 'options'.
        If you set "headers" dict object, you can set your own custom header.
        
        >>> ws = WebSocket()
        >>> ws.connect("ws://echo.websocket.org/",
        ...     headers={"User-Agent": "MyProgram"})
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
        headers.append("Upgrade: websocket")
        headers.append("Connection: Upgrade")
        if port == 80:
            hostport = host
        else:
            hostport = "%s:%d" % (host, port)
        headers.append("Host: %s" % hostport)
        headers.append("Origin: %s" % hostport)
   
        key = _create_sec_websocket_key()
        headers.append("Sec-WebSocket-Key: %s" % key)
        headers.append("Sec-WebSocket-Protocol: chat, superchat")
        headers.append("Sec-WebSocket-Version: %s" % VERSION)
        if "header" in options:
            headers.extend(options["header"])

        headers.append("")
        headers.append("")

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

        success = self._validate_header(resp_headers, key)
        if not success:
            self.close()
            raise WebSocketException("Invalid WebSocket Header")

        self.connected = True
    
    def _validate_header(self, headers, key):
        for k, v in HEADERS_TO_CHECK.iteritems():
            r = headers.get(k, None)
            if not r:
                return False
            r = r.lower()
            if v != r:
                return False

        result = headers.get("sec-websocket-accept", None)
        if not result:
            return False
        result = result.lower()
        
        value = key + "258EAFA5-E914-47DA-95CA-C5AB0DC85B11"
        hashed = base64.encodestring(sha.sha(value).digest()).strip().lower()
        return hashed == result

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
    
    def send(self, payload, binary = False):
        """
        Send the data as string. payload must be utf-8 string or unicoce.
        """
        frame = ABNF.create_frame(payload, ABNF.OPCODE_TEXT)
        data = frame.format()
        print repr(data)
        self.io_sock.send(data)
        if traceEnabled:
            logger.debug("send: " + repr(data))

    def recv(self):
        """
        Receive utf-8 string data from the server.
        """
        frame = self.read_frame()
        return frame.data

    def read_frame(self):
        header_bytes = self._recv(2)
        b1 = ord(header_bytes[0])
        fin = b1 >> 7 & 1
        rsv1 = b1 >> 6 & 1
        rsv2 = b1 >> 5 & 1
        rsv3 = b1 >> 4 & 1
        opcode = b1 & 0xf
        
        b2 = ord(header_bytes[1])
        mask = b2 >> 7 & 1
        length = b2 & 0x7f

        if length == 0x7e:
            l = self._recv(2)
            length = struct.unpack("!H", l)[0]
        elif length == 0x7f:
            l = self._recv(8)
            length = struct.unpack("!Q", l)[0]
        
        data = self._recv(length)

        if mask:
            raise NotImplementedError("masked data transfer is not implemented")
        
        frame = ABNF(fin, rsv1, rsv2, rsv3, opcode, mask, data)
        return frame


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
    ws = create_connection("ws://echo.websocket.org/")
    print "Sending 'Hello, World'..."
    ws.send("Hello, World")
    print "Sent"
    print "Receiving..."
    result =  ws.recv()
    print "Received '%s'" % result
    ws.close()
