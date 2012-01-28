=================
websocket-client
=================

websocket-client module  is WebSocket client for python. This provide the low level APIs for WebSocket. All APIs are the synchronous functions.

websocket-client supports only hybi-13.

License
============

 - LGPL

Installation
=============

This module is tested on only Python 2.7.

Type "python setup.py install" or "pip install websocket-client" to install.

This module does not depend on any other module.

Example
============

Low Level API example::

    from websocket import create_connection
    ws = create_connection("ws://echo.websocket.org/")
    print "Sending 'Hello, World'..."
    ws.send("Hello, World")
    print "Sent"
    print "Reeiving..."
    result =  ws.recv()
    print "Received '%s'" % result
    ws.close()


JavaScript websocket-like API example::

  import websocket
  import thread
  import time
  
  def on_message(ws, message):
      print message
  
  def on_error(ws, error):
      print error
  
  def on_close(ws):
      print "### closed ###"
  
  def on_open(ws):
      def run(*args):
          for i in range(3):
              time.sleep(1)
              ws.send("Hello %d" % i)
          time.sleep(1)
          ws.close()
          print "thread terminating..."
      thread.start_new_thread(run, ())
  
  
  if __name__ == "__main__":
      websocket.enableTrace(True)
      ws = websocket.WebSocketApp("ws://echo.websocket.org/",
                                  on_message = on_message,
                                  on_error = on_error,
                                  on_close = on_close)
      ws.on_open = on_open
      
      ws.run_forever()

ChangeLog
============

- v0.5.1
  - delete invalid print statement.
- v0.5.0
  - support hybi-13 protocol.
- v0.4.1
  - fix incorrect custom header order(ISSUE#1)
   
