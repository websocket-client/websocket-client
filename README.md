# websocket-client

This is a fork of @liris's original
[websocket-client](https://github.com/websocket-client/websocket-client) tool and
is intended to serve as a destination for further development, since the original
project has not been updated in years. [This discussion](https://github.com/websocket-client/websocket-client/issues/644)
in the original repo helped kick off this fork.

websocket-client module is a WebSocket client for Python. It provides the
low level APIs for WebSocket. All APIs are the synchronous functions.

websocket-client supports only [hybi-13](https://tools.ietf.org/html/draft-ietf-hybi-thewebsocketprotocol-13).

## License

- BSD

## Installation

This module is tested on Python 2.7 and Python 3.4+. Python 3 support was
introduced in version 0.14.0, but is a work in progress. Thanks to
@battlemidget and @ralphbean for helping migrate this project to Python 3.

First, install the following dependencies:
- six
- backports.ssl\_match\_hostname for Python 2.x

You can install the dependencies with the command `pip install six`

You can use either `python setup.py install` or `pip install websocket-client` to
install.

## Performance

The "send" and "validate_utf8" methods are very slow in pure Python.
If you want to get better performace, please install both numpy and wsaccel.
Note that wsaccel can sometimes causes other issues.

## Examples

### wsdump.py example

The wsdump.py file, found in the /bin directory of this project, is a debug tool
that provides a functional starting point for users who wish to test the
functions of this client without substantial customization.

```python wsdump.py -h          
usage: wsdump.py [-h] [-p PROXY] [-v [VERBOSE]] [-n] [-r]
                 [-s [SUBPROTOCOLS [SUBPROTOCOLS ...]]] [-o ORIGIN]
                 [--eof-wait EOF_WAIT] [-t TEXT] [--timings]
                 [--headers HEADERS]
                 ws_url

WebSocket Simple Dump Tool

positional arguments:
  ws_url                websocket url. ex. ws://echo.websocket.org/

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
  ```

You can run this tool against the echo.websocket.org URL for a simple test:
`wsdump.py ws://echo.websocket.org/`

### HTTP proxy

This project supports WebSocket connections over a HTTP proxy. The proxy server
must allow "CONNECT" method to websocket port. The default squid proxy setting
is "ALLOWED TO CONNECT ONLY HTTPS PORT".

The current implementation of websocket-client is using the "CONNECT" method via
proxy. Here is an example of using a proxy:

``` sourceCode python
import websocket
ws = websocket.WebSocket()
ws.connect("ws://example.com/websocket", http_proxy_host="proxy_host_name", http_proxy_port=3128)
:
```

### Long-lived connection

This example is similar to how WebSocket code looks in browsers using
JavaScript.

``` sourceCode python
import websocket
try:
    import thread
except ImportError:
    import _thread as thread
import time

def on_message(ws, message):
    print(message)

def on_error(ws, error):
    print(error)

def on_close(ws):
    print("### closed ###")

def on_open(ws):
    def run(*args):
        for i in range(3):
            time.sleep(1)
            ws.send("Hello %d" % i)
        time.sleep(1)
        ws.close()
        print("thread terminating...")
    thread.start_new_thread(run, ())


if __name__ == "__main__":
    websocket.enableTrace(True)
    ws = websocket.WebSocketApp("ws://echo.websocket.org/",
                              on_message = on_message,
                              on_error = on_error,
                              on_close = on_close)
    ws.on_open = on_open
    ws.run_forever()
```

### Short-lived one-off send-receive

This is if you want to communicate a short message and disconnect
immediately when done.

```from websocket import create_connection
ws = create_connection("ws://echo.websocket.org/")
print("Sending 'Hello, World'...")
ws.send("Hello, World")
print("Sent")
print("Receiving...")
result =  ws.recv()
print("Received '%s'" % result)
ws.close()
```

If you want to customize socket options, set sockopt, as seen below:

```from websocket import create_connection
ws = create_connection("ws://echo.websocket.org/",
                        sockopt=((socket.IPPROTO_TCP, socket.TCP_NODELAY),))
```

### More advanced: custom class

You can also write your own class for the connection, if you want to handle the nitty-gritty details yourself.

```import socket
from websocket import create_connection, WebSocket
class MyWebSocket(WebSocket):
    def recv_frame(self):
        frame = super().recv_frame()
        print('yay! I got this frame: ', frame)
        return frame

ws = create_connection("ws://echo.websocket.org/",
                        sockopt=((socket.IPPROTO_TCP, socket.TCP_NODELAY, 1),), class_=MyWebSocket)
```

## FAQ

### How to disable ssl cert verification?

Set the sslopt to {"cert_reqs": ssl.CERT_NONE}. The same sslopt argument is provided
for all examples seen below.

WebSocketApp example

```ws = websocket.WebSocketApp("wss://echo.websocket.org")
ws.run_forever(sslopt={"cert_reqs": ssl.CERT_NONE})
```

create_connection example

```ws = websocket.create_connection("wss://echo.websocket.org",
  sslopt={"cert_reqs": ssl.CERT_NONE})
```

WebSocket example

```ws = websocket.WebSocket(sslopt={"cert_reqs": ssl.CERT_NONE})
ws.connect("wss://echo.websocket.org")
```

### How to disable hostname verification?

Please set sslopt to {"check_hostname": False}. (since v0.18.0)

WebSocketApp example

```ws = websocket.WebSocketApp("wss://echo.websocket.org")
ws.run_forever(sslopt={"check_hostname": False})
```

create_connection example

```ws = websocket.create_connection("wss://echo.websocket.org",
  sslopt={"check_hostname": False})
```

WebSocket example

```ws = websocket.WebSocket(sslopt={"check_hostname": False})
ws.connect("wss://echo.websocket.org")
```

## How to enable [SNI](http://en.wikipedia.org/wiki/Server_Name_Indication)?

SNI support is available for Python 2.7.9+ and 3.2+.
It will be enabled automatically whenever possible.

## Using Subprotocols

The WebSocket RFC [outlines the usage of subprotocols](https://tools.ietf.org/html/rfc6455#section-1.9).
The subprotocol can be specified as in the example below:

`ws = websocket.create_connection("ws://example.com/websocket", subprotocols=["binary", "base64"])`
