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
    Foundation, Inc., 51 Franklin Street, Fifth Floor,
    Boston, MA  02110-1335  USA

"""
from __future__ import print_function


import six
import socket

try:
    import ssl
    from ssl import SSLError
    if hasattr(ssl, "match_hostname"):
        from ssl import match_hostname
    else:
        from backports.ssl_match_hostname import match_hostname

    HAVE_SSL = True
except ImportError:
    # dummy class of SSLError for ssl none-support environment.
    class SSLError(Exception):
        pass

    HAVE_SSL = False


if six.PY3:
    from base64 import encodebytes as base64encode
else:
    from base64 import encodestring as base64encode

import os
import errno
import struct
import threading

# websocket modules
from ._exceptions import *
from ._abnf import *
from ._socket import *
from ._utils import *
from ._url import *
from ._logging import *
from ._http import *
from ._handshake import *

"""
websocket python client.
=========================

This version support only hybi-13.
Please see http://tools.ietf.org/html/rfc6455 for protocol.
"""


def create_connection(url, timeout=None, **options):
    """
    connect to url and return websocket object.

    Connect to url and return the WebSocket object.
    Passing optional timeout parameter will set the timeout on the socket.
    If no timeout is supplied,
    the global default timeout setting returned by getdefauttimeout() is used.
    You can customize using 'options'.
    If you set "header" list object, you can set your own custom header.

    >>> conn = create_connection("ws://echo.websocket.org/",
         ...     header=["User-Agent: MyProgram",
         ...             "x-custom: header"])


    timeout: socket timeout time. This value is integer.
             if you set None for this value,
             it means "use default_timeout value"


    options: "header" -> custom http header list.
             "cookie" -> cookie value.
             "http_proxy_host" - http proxy host name.
             "http_proxy_port" - http proxy port. If not set, set to 80.
             "http_no_proxy"   - host names, which doesn't use proxy.
             "http_proxy_auth" - http proxy auth infomation.
                                    tuple of username and password.
                                    default is None
             "enable_multithread" -> enable lock for multithread.
             "sockopt" -> socket options
             "sslopt" -> ssl option
             "subprotocols" - array of available sub protocols.
                              default is None.
             "skip_utf8_validation" - skip utf8 validation.
    """
    sockopt = options.get("sockopt", [])
    sslopt = options.get("sslopt", {})
    fire_cont_frame = options.get("fire_cont_frame", False)
    enable_multithread = options.get("enable_multithread", False)
    skip_utf8_validation = options.get("skip_utf8_validation", False)
    websock = WebSocket(sockopt=sockopt, sslopt=sslopt,
                        fire_cont_frame=fire_cont_frame,
                        enable_multithread=enable_multithread,
                        skip_utf8_validation=skip_utf8_validation)
    websock.settimeout(timeout if timeout is not None else getdefaulttimeout())
    websock.connect(url, **options)
    return websock


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

    get_mask_key: a callable to produce new mask keys, see the set_mask_key
      function's docstring for more details
    sockopt: values for socket.setsockopt.
        sockopt must be tuple and each element is argument of sock.setscokopt.
    sslopt: dict object for ssl socket option.
    fire_cont_frame: fire recv event for each cont frame. default is False
    enable_multithread: if set to True, lock send method.
    skip_utf8_validation: skip utf8 validation.
    """

    def __init__(self, get_mask_key=None, sockopt=None, sslopt=None,
                 fire_cont_frame=False, enable_multithread=False,
                 skip_utf8_validation=False):
        """
        Initalize WebSocket object.
        """
        if sockopt is None:
            sockopt = []
        if sslopt is None:
            sslopt = {}
        self.connected = False
        self.sock = None
        self._timeout = None
        self.sockopt = sockopt
        self.sslopt = sslopt
        self.get_mask_key = get_mask_key
        self.fire_cont_frame = fire_cont_frame
        self.skip_utf8_validation = skip_utf8_validation
        # Buffers over the packets from the layer beneath until desired amount
        # bytes of bytes are received.
        self._recv_buffer = []
        # These buffer over the build-up of a single frame.
        self._frame_buffer = FrameBuffer()
        self._cont_data = None
        self._recving_frames = None
        if enable_multithread:
            self.lock = threading.Lock()
        else:
            self.lock = NoLock()

        self.subprotocol = None

    def fileno(self):
        return self.sock.fileno()

    def set_mask_key(self, func):
        """
        set function to create musk key. You can custumize mask key generator.
        Mainly, this is for testing purpose.

        func: callable object. the fuct must 1 argument as integer.
              The argument means length of mask key.
              This func must be return string(byte array),
              which length is argument specified.
        """
        self.get_mask_key = func

    def gettimeout(self):
        """
        Get the websocket timeout(second).
        """
        return self._timeout

    def settimeout(self, timeout):
        """
        Set the timeout to the websocket.

        timeout: timeout time(second).
        """
        self._timeout = timeout
        if self.sock:
            self.sock.settimeout(timeout)

    timeout = property(gettimeout, settimeout)

    def connect(self, url, **options):
        """
        Connect to url. url is websocket url scheme.
        ie. ws://host:port/resource
        You can customize using 'options'.
        If you set "header" list object, you can set your own custom header.

        >>> ws = WebSocket()
        >>> ws.connect("ws://echo.websocket.org/",
                ...     header=["User-Agent: MyProgram",
                ...             "x-custom: header"])

        timeout: socket timeout time. This value is integer.
                 if you set None for this value,
                 it means "use default_timeout value"

        options: "header" -> custom http header list.
                 "cookie" -> cookie value.
                 "http_proxy_host" - http proxy host name.
                 "http_proxy_port" - http proxy port. If not set, set to 80.
                 "http_no_proxy"   - host names, which doesn't use proxy.
                 "http_proxy_auth" - http proxy auth infomation.
                                     tuple of username and password.
                                     defualt is None
                 "subprotocols" - array of available sub protocols.
                                  default is None.

        """
        if "sockopt" in options:
            del options["sockopt"]
        self.sock, addrs = connect(url, self.sockopt, self.sslopt, self.timeout, **options)

        try:
            self.subprotocol = handshake(self.sock, *addrs, **options)
            self.connected = True
        except:
            self.sock.close()
            self.sock = None
            raise

    def send(self, payload, opcode=ABNF.OPCODE_TEXT):
        """
        Send the data as string.

        payload: Payload must be utf-8 string or unicode,
                  if the opcode is OPCODE_TEXT.
                  Otherwise, it must be string(byte array)

        opcode: operation code to send. Please see OPCODE_XXX.
        """

        frame = ABNF.create_frame(payload, opcode)
        return self.send_frame(frame)

    def send_frame(self, frame):
        """
        Send the data frame.

        frame: frame data created  by ABNF.create_frame

        >>> ws = create_connection("ws://echo.websocket.org/")
        >>> frame = ABNF.create_frame("Hello", ABNF.OPCODE_TEXT)
        >>> ws.send_frame(frame)
        >>> cont_frame = ABNF.create_frame("My name is ", ABNF.OPCODE_CONT, 0)
        >>> ws.send_frame(frame)
        >>> cont_frame = ABNF.create_frame("Foo Bar", ABNF.OPCODE_CONT, 1)
        >>> ws.send_frame(frame)

        """
        if self.get_mask_key:
            frame.get_mask_key = self.get_mask_key
        data = frame.format()
        length = len(data)
        trace("send: " + repr(data))

        with self.lock:
            while data:
                l = self._send(data)
                data = data[l:]

        return length

    def send_binary(self, payload):
        return self.send(payload, ABNF.OPCODE_BINARY)

    def ping(self, payload=""):
        """
        send ping data.

        payload: data payload to send server.
        """
        if isinstance(payload, six.text_type):
            payload = payload.encode("utf-8")
        self.send(payload, ABNF.OPCODE_PING)

    def pong(self, payload):
        """
        send pong data.

        payload: data payload to send server.
        """
        if isinstance(payload, six.text_type):
            payload = payload.encode("utf-8")
        self.send(payload, ABNF.OPCODE_PONG)

    def recv(self):
        """
        Receive string data(byte array) from the server.

        return value: string(byte array) value.
        """
        opcode, data = self.recv_data()
        if six.PY3 and opcode == ABNF.OPCODE_TEXT:
            return data.decode("utf-8")
        elif opcode == ABNF.OPCODE_TEXT or opcode == ABNF.OPCODE_BINARY:
            return data
        else:
            return ''

    def recv_data(self, control_frame=False):
        """
        Recieve data with operation code.

        control_frame: a boolean flag indicating whether to return control frame
        data, defaults to False

        return  value: tuple of operation code and string(byte array) value.
        """
        opcode, frame = self.recv_data_frame(control_frame)
        return opcode, frame.data

    def recv_data_frame(self, control_frame=False):
        """
        Recieve data with operation code.

        control_frame: a boolean flag indicating whether to return control frame
        data, defaults to False

        return  value: tuple of operation code and string(byte array) value.
        """
        while True:
            frame = self.recv_frame()
            if not frame:
                # handle error:
                # 'NoneType' object has no attribute 'opcode'
                raise WebSocketProtocolException("Not a valid frame %s" % frame)
            elif frame.opcode in (ABNF.OPCODE_TEXT, ABNF.OPCODE_BINARY, ABNF.OPCODE_CONT):
                if not self._recving_frames and frame.opcode == ABNF.OPCODE_CONT:
                    raise WebSocketProtocolException("Illegal frame")
                if self._recving_frames and frame.opcode in (ABNF.OPCODE_TEXT, ABNF.OPCODE_BINARY):
                    raise WebSocketProtocolException("Illegal frame")

                if self._cont_data:
                    self._cont_data[1] += frame.data
                else:
                    if frame.opcode in (ABNF.OPCODE_TEXT, ABNF.OPCODE_BINARY):
                        self._recving_frames = frame.opcode
                    self._cont_data = [frame.opcode, frame.data]

                if frame.fin:
                    self._recving_frames = None

                if frame.fin or self.fire_cont_frame:
                    data = self._cont_data
                    self._cont_data = None
                    frame.data = data[1]
                    if not self.fire_cont_frame and data[0] == ABNF.OPCODE_TEXT and not self.skip_utf8_validation and not validate_utf8(frame.data):
                        raise WebSocketPayloadException("cannot decode: " + repr(frame.data))
                    return [data[0], frame]

            elif frame.opcode == ABNF.OPCODE_CLOSE:
                self.send_close()
                return (frame.opcode, frame)
            elif frame.opcode == ABNF.OPCODE_PING:
                if len(frame.data) < 126:
                    self.pong(frame.data)
                else:
                    raise WebSocketProtocolException("Ping message is too long")
                if control_frame:
                    return (frame.opcode, frame)
            elif frame.opcode == ABNF.OPCODE_PONG:
                if control_frame:
                    return (frame.opcode, frame)

    def recv_frame(self):
        """
        recieve data as frame from server.

        return value: ABNF frame object.
        """
        frame_buffer = self._frame_buffer
        # Header
        if frame_buffer.has_received_header():
            frame_buffer.recv_header(self._recv_strict)
        (fin, rsv1, rsv2, rsv3, opcode, has_mask, _) = frame_buffer.header

        # Frame length
        if frame_buffer.has_received_length():
            frame_buffer.recv_length(self._recv_strict)
        length = frame_buffer.length

        # Mask
        if frame_buffer.has_received_mask():
            frame_buffer.recv_mask(self._recv_strict)
        mask = frame_buffer.mask

        # Payload
        payload = self._recv_strict(length)
        if has_mask:
            payload = ABNF.mask(mask, payload)

        # Reset for next frame
        frame_buffer.clear()

        frame = ABNF(fin, rsv1, rsv2, rsv3, opcode, has_mask, payload)
        frame.validate(self.skip_utf8_validation)

        return frame

    def send_close(self, status=STATUS_NORMAL, reason=six.b("")):
        """
        send close data to the server.

        status: status code to send. see STATUS_XXX.

        reason: the reason to close. This must be string or bytes.
        """
        if status < 0 or status >= ABNF.LENGTH_16:
            raise ValueError("code is invalid range")
        self.connected = False
        self.send(struct.pack('!H', status) + reason, ABNF.OPCODE_CLOSE)

    def close(self, status=STATUS_NORMAL, reason=six.b("")):
        """
        Close Websocket object

        status: status code to send. see STATUS_XXX.

        reason: the reason to close. This must be string.
        """
        if self.connected:
            if status < 0 or status >= ABNF.LENGTH_16:
                raise ValueError("code is invalid range")

            try:
                self.connected = False
                self.send(struct.pack('!H', status) + reason, ABNF.OPCODE_CLOSE)
                timeout = self.sock.gettimeout()
                self.sock.settimeout(3)
                try:
                    frame = self.recv_frame()
                    if isEnableForError():
                        recv_status = struct.unpack("!H", frame.data)[0]
                        if recv_status != STATUS_NORMAL:
                            error("close status: " + repr(recv_status))
                except:
                    pass
                self.sock.settimeout(timeout)
                self.sock.shutdown(socket.SHUT_RDWR)
            except:
                pass

        self.shutdown()

    def abort(self):
        """
        Low-level asynchonous abort, wakes up other threads that are waiting in recv_*
        """
        if self.connected:
            self.sock.shutdown(socket.SHUT_RDWR)

    def shutdown(self):
        "close socket, immediately."
        if self.sock:
            self.sock.close()
            self.sock = None
            self.connected = False

    def _send(self, data):
        return send(self.sock, data)

    def _recv(self, bufsize):
        try:
            return recv(self.sock, bufsize)
        except WebSocketConnectionClosedException:
            if self.sock:
                self.sock.close()
            self.sock = None
            self.connected = False
            raise
        except:
            raise

    def _recv_strict(self, bufsize):
        shortage = bufsize - sum(len(x) for x in self._recv_buffer)
        while shortage > 0:
            bytes = self._recv(shortage)
            self._recv_buffer.append(bytes)
            shortage -= len(bytes)

        unified = six.b("").join(self._recv_buffer)

        if shortage == 0:
            self._recv_buffer = []
            return unified
        else:
            self._recv_buffer = [unified[bufsize:]]
            return unified[:bufsize]
