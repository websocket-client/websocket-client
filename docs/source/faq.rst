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
If you want to get better performance, install wsaccel. While
websocket-client does not depend on wsaccel, it will be used if
available. wsaccel doubles the speed of UTF8 validation and
offers a very minor 10% performance boost when masking the
payload data as part of the ``send`` process. Numpy used to
be a suggested alternative, but
`issue #687 <https://github.com/websocket-client/websocket-client/issues/687>`_
found it didn't help.

How to troubleshoot an unclear callback error?
===================================================

To get more information about a callback error, you can
specify a custom ``on_error()`` function that raises errors
to provide more information. Sample code of such a solution
is shown below, although the example URL provided will probably
not trigger an error under normal circumstances.
`Issue #377 <https://github.com/websocket-client/websocket-client/issues/60>`_
discussed this topic previously.

::

  import websocket

  def on_message(ws, message):
    print(message)

  def on_error(wsapp, err):
    print("Got a an error: ", err)

  wsapp = websocket.WebSocketApp("ws://echo.websocket.org/",
    on_message = on_message,
    on_error=on_error)
  wsapp.run_forever()

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


What else can I do with sslopts?
============================================================================

The ``sslopt`` parameter is a dictionary to which the following keys can be assigned:

* ``certfile``, ``keyfile``, ``password`` (see `SSLContext.load_cert_chain <https://docs.python.org/3/library/ssl.html#ssl.SSLContext.load_cert_chain>`_)
* ``ecdh_curve`` (see `SSLContext.set_ecdh_curve <https://docs.python.org/3/library/ssl.html#ssl.SSLContext.set_ecdh_curve>`_)
* ``ciphers`` (see `SSLContext.set_ciphers <https://docs.python.org/3/library/ssl.html#ssl.SSLContext.set_ciphers>`_)
* ``cert_reqs`` (see `SSLContext.verify_mode <https://docs.python.org/3/library/ssl.html#ssl.SSLContext.verify_mode>`_)
* ``ssl_version`` (see `SSLContext.protocol <https://docs.python.org/3/library/ssl.html#ssl.SSLContext.protocol>`_)
* ``ca_certs``, ``ca_cert_path`` (see `SSLContext.load_verify_locations <https://docs.python.org/3/library/ssl.html#ssl.SSLContext.load_verify_locations>`_)
* ``check_hostname`` (see `SSLContext.check_hostname <https://docs.python.org/3/library/ssl.html#ssl.SSLContext.check_hostname>`_)
* ``server_hostname``, ``do_handshake_on_connect``, ``suppress_ragged_eofs`` (see `SSLContext.wrap_socket <https://docs.python.org/3/library/ssl.html#ssl.SSLContext.wrap_socket>`_)

If any other SSL options are required, they can be used by creating a custom SSLContext from the python SSL library and then passing that in as the value of the ``context`` key. (since v1.2.2)

For example, if you wanted to load all of the default CA verification certificates, but also add your own additional custom CAs (of which the certs are located in the file "my_extra_CAs.cer"), you could do this:

::

    my_context = ssl.create_default_context()
    my_context.load_verify_locations('my_extra_CAs.cer')
    ws.run_forever(sslopt={'context': my_context})

Note that when passing in a custom ``context``, all of the other context-related options are ignored. In other words, only the ``server_hostname``, ``do_handshake_on_connect``, and ``suppress_ragged_eofs`` options can be used in conjunction with ``context``.

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
