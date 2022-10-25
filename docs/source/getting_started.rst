###############
Getting Started
###############

The quickest way to get started with this library is to use the `_wsdump.py
script <https://github.com/websocket-client/websocket-client/blob/master/websocket/_wsdump.py>`_.
For an easy example, run the following:

::

  python _wsdump.py ws://echo.websocket.events/ -t "hello world"

The above command will provide you with an interactive terminal to communicate
with the echo.websocket.events server. This server will echo back any message you
send it.

The wsdump.py script has many additional options too, so it's a great way to try
using this library without writing any custom code. The output of
``python wsdump.py -h`` is seen below, showing the additional options available.

::

  python wsdump.py -h
  usage: wsdump.py [-h] [-p PROXY] [-v [VERBOSE]] [-n] [-r]
                   [-s [SUBPROTOCOLS [SUBPROTOCOLS ...]]] [-o ORIGIN]
                   [--eof-wait EOF_WAIT] [-t TEXT] [--timings]
                   [--headers HEADERS]
                   ws_url

  WebSocket Simple Dump Tool

  positional arguments:
    ws_url                websocket url. ex. ws://echo.websocket.events/

  optional arguments:
    -h, --help            show this help message and exit
    -p PROXY, --proxy PROXY
                          proxy url. ex. http://127.0.0.1:8080
    -v [VERBOSE], --verbose [VERBOSE]
                          set verbose mode. If set to 1, show opcode. If set to
                          2, enable to trace websocket module
    -n, --nocert          Ignore invalid SSL cert
    -r, --raw             raw output
    -s [SUBPROTOCOLS [SUBPROTOCOLS ...]], --subprotocols [SUBPROTOCOLS [SUBPROTOCOLS ...]]
                          Set subprotocols
    -o ORIGIN, --origin ORIGIN
                          Set origin
    --eof-wait EOF_WAIT   wait time(second) after 'EOF' received.
    -t TEXT, --text TEXT  Send initial text
    --timings             Print timings in seconds
    --headers HEADERS     Set custom headers. Use ',' as separator
