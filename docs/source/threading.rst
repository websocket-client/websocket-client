#########
Threading
#########

Importance of enable_multithread
======================================

The ``enable_multithread`` variable should be set to ``True`` when
working with multiple threads. If ``enable_multithread`` is not
set to ``True``, websocket-client will act asynchronously and
not be thread safe. This variable should be enabled by default
starting with the 1.1.0 release, but had a default value of ``False``
in older versions. See issues
`#591 <https://github.com/websocket-client/websocket-client/issues/591>`_
and
`#507 <https://github.com/websocket-client/websocket-client/issues/507>`_
for related issues.

asyncio library usage
=======================
Issue `#496 <https://github.com/websocket-client/websocket-client/issues/496>`_
indicates that websocket-client is not compatible with asyncio. The 
`engine-io project <https://github.com/miguelgrinberg/python-engineio/>`_,
which is used in a popular socket-io client, specifically uses websocket-client
as a dependency only in places where asyncio is not used. If asyncio is an
important part of your project, you might consider using another websockets library.
However, some simple use cases, such as asynchronously receiving data, may be
a place to use asyncio. Here is one snippet showing how asynchronous listening
might be implemented.

::

  async def mylisten(ws):
      result = await asyncio.get_event_loop().run_in_executor(None, ws.recv)
      return result


threading library usage
==========================

The websocket-client library has some built-in threading support
provided by the ``threading`` library. You will see ``import threading``
in some of this project's code. The
`echoapp_client.py example <https://github.com/websocket-client/websocket-client/blob/master/examples/echoapp_client.py>`_
is a good illustration of how ``threading`` can be used in the websocket-client library.
Another example is found in
`an external site's documentation <https://support.kraken.com/hc/en-us/articles/360043283472-Python-WebSocket-Recommended-Python-library-and-usage-examples>`_, 
which demonstrates using the _thread library, which is lower level than
the threading library.

Possible issues with threading
==================================

Further investigation into using the ``threading`` module is seen in
issue `#612 <https://github.com/websocket-client/websocket-client/issues/612>`_
which illustrates one situation where using the threading module can impact
the observed behavior of this library. The first code example below does
not trigger the ``on_close()`` function, but the second code example does
trigger the ``on_close()`` function. The highlighted rows show the lines added
exclusively in the second example. This threading approach is identical to the
`echoapp_client.py example <https://github.com/websocket-client/websocket-client/blob/master/examples/echoapp_client.py>`_.
However, further testing found that some WebSocket servers, such as
ws://echo.websocket.events, do not trigger the ``on_close()`` function.


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

  def on_close(ws, close_status_code, close_msg):
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

  def on_close(ws, close_status_code, close_msg):
      print(">>>>>>CLOSED")

  wsapp = websocket.WebSocketApp("wss://api.bitfinex.com/ws/1", on_open=on_open, on_message=on_message, on_close=on_close)
  wsapp.run_forever()


Another example of code that does not trigger `on_close` is below. The fix is to use a timer.

**NOT working on_close() example, with sleep delay**

.. code-block:: python
  :emphasize-lines: 11

  import websocket
  from threading import Thread
  import sys
  import time

  def on_close(ws, close_status_code, close_msg):
      print("### closed ###")

  def on_message(ws, message):
      print(message)
      time.sleep(2)

  if __name__ == "__main__":
      websocket.enableTrace(True)
      if len(sys.argv) < 2:
          host = "ws://echo.websocket.events/"
      else:
          host = sys.argv[1]
      ws = websocket.WebSocketApp(host,
                                  on_message=on_message,
                                  on_close=on_close)
      Thread(target=ws.run_forever).start()
      time.sleep(1)
      ws.close()


**Working on_close() example, with threading delay**

.. code-block:: python
  :emphasize-lines: 11,12

  import websocket
  from threading import Thread
  import sys
  import time

  def on_close(ws, close_status_code, close_msg):
      print("### closed ###")

  def on_message(ws, message):
      print(message)
      timer = threading.Timer(2, ws.close)
      timer.start()

  if __name__ == "__main__":
      websocket.enableTrace(True)
      if len(sys.argv) < 2:
          host = "ws://echo.websocket.events/"
      else:
          host = sys.argv[1]
      ws = websocket.WebSocketApp(host,
                                  on_message=on_message,
                                  on_close=on_close)
      Thread(target=ws.run_forever).start()
      time.sleep(1)
      ws.close()


In part because threading is hard, but also because this project has (until recently)
lacked any threading documentation, there are many issues on this topic, including:

  - `#562 <https://github.com/websocket-client/websocket-client/issues/562>`_
  - `#580 <https://github.com/websocket-client/websocket-client/issues/580>`_
  - `#591 <https://github.com/websocket-client/websocket-client/issues/591>`_

