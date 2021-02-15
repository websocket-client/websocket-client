[![docs](https://readthedocs.org/projects/websocket-client/badge/?style=flat)](https://websocket-client.readthedocs.io/)
[![Build Status](https://travis-ci.com/websocket-client/websocket-client.svg?branch=master)](https://travis-ci.com/websocket-client/websocket-client)
[![codecov](https://codecov.io/gh/websocket-client/websocket-client/branch/master/graph/badge.svg?token=pcXhUQwiL3)](https://codecov.io/gh/websocket-client/websocket-client)
[![Downloads](https://pepy.tech/badge/websocket-client)](https://pepy.tech/project/websocket-client)
[![PyPI version](https://badge.fury.io/py/websocket_client.svg)](https://badge.fury.io/py/websocket_client)

# websocket-client

The websocket-client module is a WebSocket client for Python. It provides access
to low level APIs for WebSockets. All APIs are for synchronous functions.

websocket-client supports only [hybi-13](https://tools.ietf.org/html/draft-ietf-hybi-thewebsocketprotocol-13).

## License

- BSD

## Documentation

This project's documentation can be found at
[https://websocket-client.readthedocs.io/](https://websocket-client.readthedocs.io/)

## Contributing

Please see the contribution guidelines at
[https://websocket-client.readthedocs.io/en/latest/contributing.html](https://websocket-client.readthedocs.io/en/latest/contributing.html)

## Installation

First, install the following dependencies:
- six
- backports.ssl\_match\_hostname for Python 2.x

You can install the dependencies with the command `pip install six` and
`pip install backports.ssl_match_hostname`

You can use either `python setup.py install` or `pip install websocket-client`
to install. This module is tested on Python 2.7 and Python 3.4+. Python 3
support was first introduced in version 0.14.0, but is a work in progress.


## Usage Tips

Check out the documentation's FAQ for additional guidelines:
[https://websocket-client.readthedocs.io/en/latest/faq.html](https://websocket-client.readthedocs.io/en/latest/faq.html)

### Performance

The "send" and "validate_utf8" methods are very slow in pure Python.
If you want to get better performance, please install both numpy and wsaccel.
Note that wsaccel can sometimes cause other issues.

### HTTP proxy

This project supports WebSocket connections over a HTTP proxy. The proxy server
must allow "CONNECT" method to websocket port. The default squid proxy setting
is "ALLOWED TO CONNECT ONLY HTTPS PORT".

The current implementation of websocket-client is using the "CONNECT" method via
proxy. Here is an example of using a proxy:

```python
import websocket
ws = websocket.WebSocket()
ws.connect("ws://example.com/websocket", http_proxy_host="proxy_host_name", http_proxy_port=3128)
```

### Long-lived connection

This example is similar to how WebSocket code looks in browsers using
JavaScript.

```python
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

```python
from websocket import create_connection
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

```python
from websocket import create_connection
ws = create_connection("ws://echo.websocket.org/",
                        sockopt=((socket.IPPROTO_TCP, socket.TCP_NODELAY),))
```

### More advanced: custom class

You can also write your own class for the connection, if you want to handle the nitty-gritty details yourself.

```python
import socket
from websocket import create_connection, WebSocket
class MyWebSocket(WebSocket):
    def recv_frame(self):
        frame = super().recv_frame()
        print('yay! I got this frame: ', frame)
        return frame

ws = create_connection("ws://echo.websocket.org/",
                        sockopt=((socket.IPPROTO_TCP, socket.TCP_NODELAY, 1),), class_=MyWebSocket)
```

### Acknowledgements

Thanks to @battlemidget and @ralphbean for helping migrate this project to
Python 3.
