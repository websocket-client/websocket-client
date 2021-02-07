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
simple examples below.

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

Setting Timeout Value
--------------------------------

This documentation needs to be written!

Connecting through a HTTP proxy
--------------------------------

This documentation needs to be written!


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
