###
FAQ
###

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
keep the connection alive. See `issue #200 <https://github.com/websocket-client/websocket-client/issues/200>`
for possible solutions.

Using Subprotocols
====================

The WebSocket RFC
`outlines the usage of subprotocols <https://tools.ietf.org/html/rfc6455#section-1.9>`_.
The subprotocol can be specified as in the example below:

>>> ws = websocket.create_connection("ws://example.com/websocket",
  subprotocols=["binary", "base64"])
