###
FAQ
###

What about Python 2 support?
==============================

Release 0.59.0 was the last main release supporting Python 2. All
future releases 1.X.X and beyond will only support Python 3.

Why is this library slow?
===========================

The ``send`` and ``validate_utf8`` methods are very slow in pure Python.
You can disable UTF8 validation in this library (and receive a
performance enhancement) with the ``skip_utf8_validation`` parameter.
If you want to get better performance, please install both numpy and
wsaccel, and import them into your project files - these external
libraries will automatically be used when available. Note that
wsaccel can sometimes cause other issues.

How to solve the "connection is already closed" error?
===========================================================

The WebSocketConnectionClosedException, which returns the message "Connection
is already closed.", occurs when a WebSocket function such as ``send()`` or
``recv()`` is called but the WebSocket connection is already closed. One way
to handle exceptions in Python is by using
`a try/except <https://docs.python.org/3/tutorial/errors.html#handling-exceptions>`_
statement, which allows you to control what your program does if the WebSocket
connection is closed when you try to use it. In order to properly carry out
further functions with your WebSocket connection after the connection has
closed, you will need to reconnect the WebSocket, using ``connect()`` or
``create_connection()`` (from the _core.py file). The WebSocketApp ``run_forever()``
function automatically tries to reconnect when the connection is lost.

What's going on with the naming of this library?
==================================================

To install this library, you use ``pip3 install websocket-client``, while ``import
websocket`` imports this library, and PyPi lists the package as
``websocket_client``. Why is it so confusing? To see the original issue about
the choice of ``import websocket``, see
`issue #60 <https://github.com/websocket-client/websocket-client/issues/60>`_
and to read about websocket-client vs. websocket_client, see
`issue #147 <https://github.com/websocket-client/websocket-client/issues/147>`_

Is WebSocket Compression using the permessage-deflate extension supported?
============================================================================

No, `RFC 7692 <https://tools.ietf.org/html/rfc7692>`_ for WebSocket Compression
is unfortunately not supported by the websocket-client library at this time.
You can view the currently supported WebSocket features in the
latest autobahn compliance HTML report, found under the
`compliance folder. <https://github.com/websocket-client/websocket-client/tree/master/compliance>`_
If you use the ``Sec-WebSocket-Extensions: permessage-deflate`` header with
websocket-client, you will probably encounter errors, such as the ones described
in `issue #314. <https://github.com/websocket-client/websocket-client/tree/master/compliance>`_

If a connection is re-establish after getting disconnected, does the new connection continue where the previous one dropped off?
=======================================================================================================================================

The answer to this question depends on how the WebSocket server
handles new connections. If the server keeps a list of recently dropped
WebSocket connection sessions, then it may allow you to recontinue your
WebSocket connection where you left off before disconnecting. However,
this requires extra effort from the server and may create security issues.
For these reasons it is rare to encounter such a WebSocket server.
The server would need to identify each connecting client with
authentication and keep track of which data was received using a method
like TCP's SYN/ACK. That's a lot of overhead for a lightweight protocol!
Both HTTP and WebSocket connections use TCP sockets, and when a new
WebSocket connection is created, it uses a new TCP socket. Therefore,
at the TCP layer, the default behavior is to give each WebSocket
connection a separate TCP socket. This means the re-established connection
after a disconnect is the same as a completely new connection. Another
way to think about this is: what should the server do if you create two
WebSocket connections from the same client to the same server? The easiest
solution for the server is to treat each connection separately, unless
the WebSocket uses an authentication method to identify individual clients
connecting to the server.

What is the difference between recv_frame(), recv_data_frame(), and recv_data()?
==================================================================================

This is explained in
`issue #688 <https://github.com/websocket-client/websocket-client/issues/688>`_.
This information is useful if you do NOT want to use ``run.forever()`` but want
to have similar functionality. In short, ``recv_data()`` is the
recommended choice and you will need to manage ping/pong on your own, while
``run.forever()`` handles ping/pong by default.

How to disable ssl cert verification?
=======================================

Set the sslopt to ``{"cert_reqs": ssl.CERT_NONE}``. The same sslopt argument is
provided for all examples seen below.

**WebSocketApp example**

::

  ws = websocket.WebSocketApp("wss://echo.websocket.org")
  ws.run_forever(sslopt={"cert_reqs": ssl.CERT_NONE})


**create_connection example**

::

  ws = websocket.create_connection("wss://echo.websocket.org",
    sslopt={"cert_reqs": ssl.CERT_NONE})

**WebSocket example**

::

  ws = websocket.WebSocket(sslopt={"cert_reqs": ssl.CERT_NONE})
  ws.connect("wss://echo.websocket.org")


How to disable hostname verification?
=======================================

Please set sslopt to ``{"check_hostname": False}``. (since v0.18.0)

**WebSocketApp example**

::

  ws = websocket.WebSocketApp("wss://echo.websocket.org")
  ws.run_forever(sslopt={"check_hostname": False})

**create_connection example**

::

  ws = websocket.create_connection("wss://echo.websocket.org",
    sslopt={"check_hostname": False})

**WebSocket example**

::

  ws = websocket.WebSocket(sslopt={"check_hostname": False})
  ws.connect("wss://echo.websocket.org")

How to enable `SNI <http://en.wikipedia.org/wiki/Server_Name_Indication>`_?
============================================================================

SNI support is available for Python 2.7.9+ and 3.2+.
It will be enabled automatically whenever possible.

Why don't I receive all the server's message(s)?
===================================================

Depending on how long your connection exists, it can help to ping the server to
keep the connection alive. See
`issue #200 <https://github.com/websocket-client/websocket-client/issues/200>`_
for possible solutions.

Using Subprotocols
====================

The WebSocket RFC
`outlines the usage of subprotocols <https://tools.ietf.org/html/rfc6455#section-1.9>`_.
The subprotocol can be specified as in the example below:

>>> ws = websocket.create_connection("ws://example.com/websocket",
  subprotocols=["binary", "base64"])
