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
