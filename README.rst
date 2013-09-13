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

How about Python 3
===========================

py3( https://github.com/liris/websocket-client/tree/py3 ) branch is for python 3.3. Every test case is passed.
If you are using python3, please check it.

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

If you want to customize socket options, set sockopt.

sockopt example:

    from websocket import create_connection
    ws = create_connection("ws://echo.websocket.org/".
                            sockopt=((socket.IPPROTO_TCP, socket.TCP_NODELAY),) )


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


wsdump.py
============

wsdump.py is simple WebSocket test(debug) tool.

sample for echo.websocket.org::

  $ wsdump.py ws://echo.websocket.org/
  Press Ctrl+C to quit
  > Hello, WebSocket
  < Hello, WebSocket
  > How are you?
  < How are you?

Usage
---------

usage::
  wsdump.py [-h] [-v [VERBOSE]] ws_url

WebSocket Simple Dump Tool

positional arguments:
  ws_url                websocket url. ex. ws://echo.websocket.org/

optional arguments:
  -h, --help                           show this help message and exit

  -v VERBOSE, --verbose VERBOSE    set verbose mode. If set to 1, show opcode. If set to 2, enable to trace websocket module

example::

  $ wsdump.py ws://echo.websocket.org/
  $ wsdump.py ws://echo.websocket.org/ -v
  $ wsdump.py ws://echo.websocket.org/ -vv

ChangeLog
============

- v0.12.0

  - support keep alive for WebSocketApp(ISSUE#34)
  - fix some SSL bugs(ISSUE#35, #36)
  - fix "Timing out leaves websocket library in bad state"(ISSUE#37)
  - fix "WebSocketApp.run_with_no_err() silently eats all exceptions"(ISSUE#38)
  - WebSocketTimeoutException will be raised for ws/wss timeout(ISSUE#40)
  - improve wsdump message(ISSUE#42)
  - support fragmentation message(ISSUE#43)
  - fix some bugs

- v0.11.0

  - Only log non-normal close status(ISSUE#31)
  - Fix default Origin isn't URI(ISSUE#32)
  - fileno support(ISSUE#33)

- v0.10.0

  - allow to set HTTP Header to WebSocketApp(ISSUE#27)
  - fix typo in pydoc(ISSUE#28)
  - Passing a socketopt flag to the websocket constructor(ISSUE#29)
  - websocket.send fails with long data(ISSUE#30)


- v0.9.0

  - allow to set opcode in WebSocketApp.send(ISSUE#25)
  - allow to modify Origin(ISSUE#26)

- v0.8.0

  - many bug fix
  - some performance improvement

- v0.7.0

  - fixed problem to read long data.(ISSUE#12)
  - fix buffer size boundary violation

- v0.6.0

  - Patches: UUID4, self.keep_running, mask_key (ISSUE#11)
  - add wsdump.py tool 

- v0.5.2

  - fix Echo App Demo Throw Error: 'NoneType' object has no attribute 'opcode  (ISSUE#10)

- v0.5.1

  - delete invalid print statement.

- v0.5.0

  - support hybi-13 protocol.

- v0.4.1

  - fix incorrect custom header order(ISSUE#1)
   
