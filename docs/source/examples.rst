########
Examples
########

This page needs help! Please see the :ref:`contributing` page to make it better!

Creating Your First WebSocket Connection
==========================================

If you want to connect to a websocket without writing any code yourself, you can
try out the :ref:`getting started` wsdump.py script and the
`examples/ <https://github.com/websocket-client/websocket-client/tree/master/examples>`_
directory files.

You can create your first custom connection with this library using one of the
simple examples below. Note that the first WebSocket example is best for a
short-lived connection, while the WebSocketApp example is best for a long-lived
connection.

**WebSocket example**

::

  import websocket

  ws = websocket.WebSocket()
  ws.connect("ws://echo.websocket.org")
  ws.send("Hello, Server")
  print(ws.recv())
  ws.close()

**WebSocketApp example**

::

  import websocket

  def on_message(wsapp, message):
      print(message)

  wsapp = websocket.WebSocketApp("wss://stream.meetup.com/2/rsvps", on_message=on_message)
  wsapp.run_forever()

Debug and Logging Options
==========================

When you're first writing your code, you will want to make sure everything is
working as you planned. The easiest way to view the verbose connection
information is the use ``websocket.enableTrace(True)``. For example, the
following example shows how you can verify that the proper Origin header is set.

.. code-block:: python
  :emphasize-lines: 3

  import websocket

  websocket.enableTrace(True)
  ws = websocket.WebSocket()
  ws.connect("ws://echo.websocket.org", origin="testing_websockets.com")
  ws.send("Hello, Server")
  print(ws.recv())
  ws.close()

The output you will see will look something like this:

::

  --- request header ---
  GET / HTTP/1.1
  Upgrade: websocket
	Host: echo.websocket.org
	Origin: testing123.com
	Sec-WebSocket-Key: k9kFAUWNAMmf5OEMfTlOEA==
	Sec-WebSocket-Version: 13
	Connection: Upgrade


	-----------------------
	--- response header ---
	HTTP/1.1 101 Web Socket Protocol Handshake
	Access-Control-Allow-Credentials: true
	Access-Control-Allow-Headers: content-type
	Access-Control-Allow-Headers: authorization
	Access-Control-Allow-Headers: x-websocket-extensions
	Access-Control-Allow-Headers: x-websocket-version
	Access-Control-Allow-Headers: x-websocket-protocol
	Access-Control-Allow-Origin: testing123.com
	Connection: Upgrade
	Date: Sat, 06 Feb 2021 12:34:56 GMT
	Sec-WebSocket-Accept: 4hNxSu7OllvQZJ43LGpQTuR8+QA=
	Server: Kaazing Gateway
	Upgrade: websocket
	-----------------------
	send: b'\x81\x8dS\xfb\xc3a\x1b\x9e\xaf\r<\xd7\xe326\x89\xb5\x04!'
	Hello, Server
	send: b'\x88\x82 \xc3\x85E#+'


Connection Options
===================

After you can establish a basic WebSocket connection, customizing your
connection using specific options is the next step. Fortunately, this library
provides many options you can configure, such as:

* "Host" header value
* "Cookie" header value
* "Origin" header value
* WebSocket subprotocols
* Custom headers
* SSL or hostname verification
* Timeout value

For a more detailed list of the options available for the different connection
methods, check out the source code comments for each:

* `WebSocket().connect() option docs <https://websocket-client.readthedocs.io/en/latest/core.html#websocket._core.WebSocket.connect>`_
   * Related: `WebSocket.create_connection() option docs <https://websocket-client.readthedocs.io/en/latest/core.html#websocket._core.create_connection>`_
* `WebSocketApp() option docs <https://websocket-client.readthedocs.io/en/latest/app.html#websocket._app.WebSocketApp.__init__>`_
   * Related: `WebSocketApp.run_forever docs <https://websocket-client.readthedocs.io/en/latest/app.html#websocket._app.WebSocketApp.run_forever>`_

Setting Common Header Values
--------------------------------

To modify the ``Host``, ``Origin``, ``Cookie``, or ``Sec-WebSocket-Protocol``
header values of the WebSocket handshake request, pass the ``host``, ``origin``,
``cookie``, or ``subprotocols`` options to your WebSocket connection. The first
two examples show the Host, Origin, and Cookies headers being set, while the
Sec-WebSocket-Protocol header is set separately in the following example.
For debugging, remember that it is helpful to enable :ref:`Debug and Logging Options`.

**WebSocket common headers example**

::

  import websocket

  ws = websocket.WebSocket()
  ws.connect("ws://echo.websocket.org", cookie="chocolate",
    origin="testing_websockets.com", host="echo.websocket.org/websocket-client-test")

**WebSocketApp common headers example**

::

  import websocket

  def on_message(wsapp, message):
      print(message)

  wsapp = websocket.WebSocketApp("wss://stream.meetup.com/2/rsvps",
    cookie="chocolate", on_message=on_message)
  wsapp.run_forever(origin="testing_websockets.com", host="127.0.0.1")

**WebSocket subprotocols example**

::

  import websocket

  ws = websocket.WebSocket()
  ws.connect("wss://ws.kraken.com", subprotocols=["testproto"])

**WebSocketApp subprotocols example**

::

  import websocket

  def on_message(wsapp, message):
      print(message)

  wsapp = websocket.WebSocketApp("wss://ws.kraken.com",
    subprotocols=["testproto"], on_message=on_message)
  wsapp.run_forever()

Suppress Origin Header
-------------------------

There is a special ``suppress_origin`` option that can be used to remove the
``Origin`` header from connection handshake requests. The below examples
illustrate how this can be used.
For debugging, remember that it is helpful to enable :ref:`Debug and Logging Options`.

**WebSocket suppress origin example**

::

  import websocket

  ws = websocket.WebSocket()
  ws.connect("ws://echo.websocket.org", suppress_origin=True)

**WebSocketApp suppress origin example**

::

  import websocket

  def on_message(wsapp, message):
      print(message)

  wsapp = websocket.WebSocketApp("wss://stream.meetup.com/2/rsvps",
    on_message=on_message)
  wsapp.run_forever(suppress_origin=True)

Setting Custom Header Values
--------------------------------

Setting custom header values, other than ``Host``, ``Origin``, ``Cookie``, or
``Sec-WebSocket-Protocol`` (which are addressed above), in the WebSocket
handshake request is similar to setting common header values. Use the ``header``
option to provide custom header values in a list or dict.
For debugging, remember that it is helpful to enable :ref:`Debug and Logging Options`.

**WebSocket custom headers example**

::

  import websocket

  ws = websocket.WebSocket()
  ws.connect("ws://echo.websocket.org",
    header={"CustomHeader1":"123", "NewHeader2":"Test"})

**WebSocketApp custom headers example**

::

  import websocket

  def on_message(wsapp, message):
      print(message)

  wsapp = websocket.WebSocketApp("wss://stream.meetup.com/2/rsvps",
    header={"CustomHeader1":"123", "NewHeader2":"Test"}, on_message=on_message)
  wsapp.run_forever()

Disabling SSL or Hostname Verification
---------------------------------------

See the relevant :ref:`FAQ` page for instructions.

Using a Custom Class
--------------------------------

You can also write your own class for the connection, if you want to handle
the nitty-gritty connection details yourself.

::

  import socket
  from websocket import create_connection, WebSocket
  class MyWebSocket(WebSocket):
    def recv_frame(self):
        frame = super().recv_frame()
        print('yay! I got this frame: ', frame)
        return frame

  ws = create_connection("ws://echo.websocket.org/",
                        sockopt=((socket.IPPROTO_TCP, socket.TCP_NODELAY, 1),), class_=MyWebSocket)


Setting Timeout Value
--------------------------------

The _socket.py file contains the functions ``setdefaulttimeout()`` and
``getdefaulttimeout()``. These two functions set the global ``_default_timeout``
value, which sets the socket timeout value (in seconds). These two functions
should not be confused with the similarly named ``settimeout()`` and
``gettimeout()`` functions found in the _core.py file. With WebSocketApp, the
``run_forever()`` function gets assigned the timeout `from getdefaulttimeout()
<https://github.com/websocket-client/websocket-client/blob/29c15714ac9f5272e1adefc9c99b83420b409f63/websocket/_app.py#L248>`_.
When the timeout value is reached, the exception WebSocketTimeoutException is
triggered by the _socket.py ``send()`` and ``recv()`` functions. Additional timeout
values can be found in other locations in this library,
including the ``close()`` function of the WebSocket class and the
``create_connection()`` function of the WebSocket class.

The WebSocket timeout example below shows how an exception is triggered after
no response is received from the server after 5 seconds.

**WebSocket timeout example**

::

  import websocket

  ws = websocket.WebSocket()
  ws.connect("ws://echo.websocket.org", timeout=5)
  #ws.send("Hello, Server") # Commented out to trigger WebSocketTimeoutException
  print(ws.recv())
  # Program should end with a WebSocketTimeoutException

The WebSocketApp timeout example works a bit differently than the WebSocket
example. Because WebSocketApp handles long-lived connections, it does not
timeout after a certain amount of time without receiving a message. Instead, a
timeout is triggered if no connection response is received from the server after
the timeout interval (5 seconds in the example below).

**WebSocketApp timeout example**

::

  import websocket

  def on_error(wsapp, err):
    print("Got a an error: ", err)

  websocket.setdefaulttimeout(5)
  wsapp = websocket.WebSocketApp("ws://nexus-websocket-a.intercom.io",
    on_error=on_error)
  wsapp.run_forever()
  # Program should print a "timed out" error message


Connecting through a HTTP proxy
--------------------------------

The example below show how to connect through a HTTP proxy. Note that this
library does support authentication to a proxy using the ``http_proxy_auth``
parameter. Be aware that the current implementation of websocket-client uses
the "CONNECT" method, and the proxy server must allow the "CONNECT" method. For
example, the squid proxy only allows the "CONNECT" method
`on HTTPS ports <https://wiki.squid-cache.org/Features/HTTPS#CONNECT_tunnel>`_
by default.

**WebSocket proxy example**

::

  import websocket

  ws = websocket.WebSocket()
  ws.connect("ws://echo.websocket.org",
    http_proxy_host="127.0.0.1", http_proxy_port="8080")
  ws.send("Hello, Server")
  print(ws.recv())
  ws.close()

**WebSocketApp proxy example**

`Work in progress - coming soon`


Using Unix Domain Sockets
--------------------------------

You can also connect to a WebSocket server hosted on a unix domain socket.
Just use the ``socket`` option when creating your connection.

::

  import socket
  from websocket import create_connection
  my_socket = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
  my_socket.connect("/path/to/my/unix.socket")

  ws = create_connection("ws://localhost/", # Dummy URL
                          socket = my_socket,
                          sockopt=((socket.SOL_SOCKET, socket.SO_KEEPALIVE, 1),))

Post-connection features
==========================

You can see a summary of this library's supported WebSocket features by either
running the autobahn test suite against this client, or by reviewing a recently
run autobahn report, available as a .html file in the /compliance directory.

Ping/Pong Usage
--------------------------------

The WebSocket specification defines
`ping <https://tools.ietf.org/html/rfc6455#section-5.5.2>`_ and
`pong <https://tools.ietf.org/html/rfc6455#section-5.5.3>`_
message opcodes as part of the protocol. These can serve as a way to keep a
long-lived connection active even if data is not being transmitted. However, if
a blocking event is happening, there may be some issues with ping/pong. The
below examples demonstrate how ping and pong can be sent by this library. You
can get additional debugging information by using
`Wireshark <https://www.wireshark.org/>`_
to view the ping and pong messages being sent. In order for Wireshark to
identify the WebSocket protocol properly, it should observe the initial HTTP
handshake and the HTTP 101 response in cleartext (without encryption) -
otherwise the WebSocket messages may be categorized as TCP or TLS messages.
For debugging, remember that it is helpful to enable :ref:`Debug and Logging Options`.

**WebSocket ping/pong example**

This example is best for a quick test where you want to check the effect of a
ping, or where situations where you want to customize when the ping is sent.
This type of connection does not automatically respond to a "ping" with a "pong".

::

  import websocket

  websocket.enableTrace(True)
  ws = websocket.WebSocket()
  ws.connect("ws://echo.websocket.org")
  ws.ping()
  ws.pong()
  ws.close()

**WebSocketApp ping/pong example**

This example, and ``run_forever()`` in general, is better for long-lived connections.
If a server needs a regular ping to keep the connection alive, this is probably
the option you will want to use. The ``run_forever()`` function will automatically
send a "pong" when it receives a "ping", per the specification.

::

  import websocket

  def on_message(wsapp, message):
      print(message)

  def on_ping(wsapp, message):
      print("Got a ping!")

  def on_pong(wsapp, message):
      print("Got a pong! No need to respond")

  wsapp = websocket.WebSocketApp("wss://stream.meetup.com/2/rsvps",
    on_message=on_message, on_ping=on_ping, on_pong=on_pong)
  wsapp.run_forever(ping_interval=10, ping_timeout=60)

Real-world Examples
=========================

Other projects that depend on websocket-client may be able to illustrate more
complex use cases for this library. A list of 600+ dependent projects is found
`on libraries.io <https://libraries.io/pypi/websocket-client/dependents>`_, and
a few of the projects using websocket-client are listed below:

- `https://github.com/docker/compose <https://github.com/docker/compose>`_
- `https://github.com/apache/airflow <https://github.com/apache/airflow>`_
- `https://github.com/docker/docker-py <https://github.com/docker/docker-py>`_
- `https://github.com/scrapinghub/slackbot <https://github.com/scrapinghub/slackbot>`_
- `https://github.com/slackapi/python-slack-sdk <https://github.com/slackapi/python-slack-sdk>`_
- `https://github.com/wee-slack/wee-slack <https://github.com/wee-slack/wee-slack>`_
- `https://github.com/aluzzardi/wssh/ <https://github.com/aluzzardi/wssh/>`_
- `https://github.com/miguelgrinberg/python-socketio <https://github.com/miguelgrinberg/python-socketio>`_
- `https://github.com/invisibleroads/socketIO-client <https://github.com/invisibleroads/socketIO-client>`_
- `https://github.com/s4w3d0ff/python-poloniex <https://github.com/s4w3d0ff/python-poloniex>`_
- `https://github.com/Ape/samsungctl <https://github.com/Ape/samsungctl>`_
- `https://github.com/xchwarze/samsung-tv-ws-api <https://github.com/xchwarze/samsung-tv-ws-api>`_
- `https://github.com/andresriancho/websocket-fuzzer <https://github.com/andresriancho/websocket-fuzzer>`_
