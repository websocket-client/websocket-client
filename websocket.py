import socket
from urlparse import urlparse
import random


class ConnectionClosedException(Exception):
    pass

default_timeout = None

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
    parsed = urlparse(url)
    if parsed.hostname:
        hostname = parsed.hostname
    else:
        raise ValueError("hostname is invalid")
    
    if parsed.scheme == "ws":
        if parsed.port:
            port = parsed.port
        else:
            port = 80
    else:
        raise ValueError("scheme %s is invalid" % parsed.scheme)
    
    if parsed.path:
        resource = parsed.path
    else:
        resource = "/"
    
    return (hostname, port, resource)


def create_connection(url, timeout=None):
    """
    connect to url and return websocket object.

    Connect to url and return the WebSocket object.
    Passing optional timeout parameter will set the timeout on the socket.
    If no timeout is supplied, the global default timeout setting returned by getdefauttimeout() is used.
    """
    try:
        websock = WebSocket()
        websock.settimeout(timeout != None and timeout or default_timeout)
        websock.connect(url)
        return websock
    except Exception, e:
        #websock.close()
        raise e

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
    

class WebSocket(object):
    def __init__(self):
        """
        Initalize WebSocket object.
        """
        self.sock = socket.socket()

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
    
    def connect(self, url):
        """
        Connect to url. url is websocket url scheme. ie. ws://host:port/resource
        """
        hostname, port, resource = _parse_url(url)
        self.sock.connect((hostname, port))
        self._handshake(hostname, port, resource)

    def _handshake(self, host, port, resource):
        sock = self.sock
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
        # headers.append("Sec-WebSocket-Key1: %s" % key_1)
        number_2, key_2 = _create_sec_websocket_key()
        # headers.append("Sec-WebSocket-Key2: %s" % key_2)
        
        header_str = "\r\n".join(headers)
        sock.send(header_str)
        sock.send("\r\n\r\n")
        key3 = _create_key3()
        #sock.send(key3)

        while True:
            line = self._recv_line()
            # TODO: check handshake response
            if line == "\r\n":
                break
    
    def send(self, payload):
        """
        Send the data as string. payload must be utf-8 string or unicoce.
        """
        if isinstance(payload, unicode):
            payload = payload.encode("utf-8")
        self.sock.send("".join(["\x00", payload, "\xff"]))

    def recv(self):
        """
        Reeive utf-8 string data from the server.
        """
        bytes = []
        while True:
            b = self._recv(1)
            if b == "\xff":
                break
            elif b == "\x00":
                # start bytes
                pass
            else:
                bytes.append(b)
        return "".join(bytes)

    def close(self):
        """
        Close Websocket object
        """
        self.sock.close()
        
    def _recv(self, bufsize):
        bytes = self.sock.recv(bufsize)
        if not bytes:
            raise ConnectionClosedException()
        return bytes

    def _recv_line(self):
        line = []
        while True:
            c = self._recv(1)
            line.append(c)
            if c == "\n":
                break
        return "".join(line)
            
        

if __name__ == "__main__":
    ws = create_connection("ws://localhost:5000/chat")
    print "Sending 'Hello, World'..."
    ws.send("Hello, World")
    print "Sent"
    print "Reeiving..."
    result =  ws.recv()
    print "Received '%s'" % result
        




