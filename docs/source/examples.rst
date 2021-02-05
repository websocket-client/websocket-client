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

Connection Options
===================

After you can establish a basic WebSocket connection, customizing your
connection using specific options is the next step. Fortunately, this library
provides many options you can configure, such as:

* "Host:" header value
* "Cookie:" header value
* "Origin:" header value
* Timeout value
* WebSocket subprotocols
* Custom headers

Setting Common Header Values
--------------------------------


Setting Custom Header Values
--------------------------------


Setting Subprotocols Values
--------------------------------


Setting Timeout Value
--------------------------------
