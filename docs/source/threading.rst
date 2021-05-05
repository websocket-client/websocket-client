#########
Threading
#########

*Warning:* The thread management documentation for this project is somewhat lacking.
If asynchronous threading is a critical part of you project, you may
want to investigate a more robust solution.

Multithreading in the websocket-client library is handled using the ``threading``
module. You can see ``import threading`` in some of this project's
code. The
`echoapp_client.py example <https://github.com/websocket-client/websocket-client/blob/master/examples/echoapp_client.py>`_.
is a good illustration of how threading can be used in the websocket-client library.
Issue `#496 <https://github.com/websocket-client/websocket-client/issues/496>`_
indicates that websocket-client is not compatible with asyncio. However, some simple
use cases, such as asyncronously receiving data, may be a convenient place to use asyncio.
The following code snippet shows how asyncronous listening might be implemented.

::

  async def mylisten(ws):
      result = await asyncio.get_event_loop().run_in_executor(None, ws.recv)
      return result


The ``enable_multithread`` variable is also a factor when handling multiple threads.
When using WebSocketApp, ``enable_multithread`` is only set
`when ping_interval is set <https://github.com/websocket-client/websocket-client/blob/7466b961f68bda3c17d2aa4701fd145abf3474ed/websocket/_app.py#L290>`_.
When WebSocketApp is not used, ``enable_multithread`` can be set to a user-specified value, and this value
will `determine the thread locking <https://github.com/websocket-client/websocket-client/blob/7466b961f68bda3c17d2aa4701fd145abf3474ed/websocket/_core.py#L103>`_.


Further investigation into using the ``threading`` module is seen in
issue `#612 <https://github.com/websocket-client/websocket-client/issues/612>`_
which illustrates on situation where using the threading module can impact
the observed behavior of this library. The first code example below does
not trigger the on_close() function, but the second code example does
trigger the on_close() function. The highlighted rows show the lines
added exclusively in the second example. This threading approach is identical
to the `echoapp_client.py example <https://github.com/websocket-client/websocket-client/blob/master/examples/echoapp_client.py>`_.
However, further testing found that some WebSocket servers, such as
ws://echo.websocket.org, do not trigger the ``on_close()`` function.


**NOT working on_close() example, without threading**

::

  import websocket

  websocket.enableTrace(True)

  def on_open(ws):
      ws.send("hi")

  def on_message(ws, message):
      print(message)
      ws.close()
      print("Message received...")

  def on_close(ws):
      print(">>>>>>CLOSED")

  wsapp = websocket.WebSocketApp("wss://api.bitfinex.com/ws/1", on_open=on_open, on_message=on_message, on_close=on_close)
  wsapp.run_forever()


**Working on_close() example, with threading**

.. code-block:: python
  :emphasize-lines: 2,10,15

  import websocket
  import threading

  websocket.enableTrace(True)

  def on_open(ws):
      ws.send("hi")

  def on_message(ws, message):
      def run(*args):
          print(message)
          ws.close()
          print("Message received...")

      threading.Thread(target=run).start()

  def on_close(ws):
      print(">>>>>>CLOSED")

  wsapp = websocket.WebSocketApp("wss://api.bitfinex.com/ws/1", on_open=on_open, on_message=on_message, on_close=on_close)
  wsapp.run_forever()

TODO: Add an example of using ws.recv() in a non-blocking manner, as asked in
`issue #416 <https://github.com/websocket-client/websocket-client/issues/416>`_

In part because threading is hard, but also because this project has (until recently)
lacked any threading documentation, there are many issues on this topic, including:

  - `#562 <https://github.com/websocket-client/websocket-client/issues/562>`_
  - `#580 <https://github.com/websocket-client/websocket-client/issues/580>`_
  - `#591 <https://github.com/websocket-client/websocket-client/issues/591>`_

