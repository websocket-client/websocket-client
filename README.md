[![docs](https://readthedocs.org/projects/websocket-client/badge/?style=flat)](https://websocket-client.readthedocs.io/)
[![Build Status](https://github.com/websocket-client/websocket-client/actions/workflows/build.yml/badge.svg)](https://github.com/websocket-client/websocket-client/actions/workflows/build.yml)
[![codecov](https://codecov.io/gh/websocket-client/websocket-client/branch/master/graph/badge.svg?token=pcXhUQwiL3)](https://codecov.io/gh/websocket-client/websocket-client)
[![PyPI Downloads](https://pepy.tech/badge/websocket-client)](https://pepy.tech/project/websocket-client)
[![PyPI version](https://img.shields.io/pypi/v/websocket_client)](https://pypi.org/project/websocket_client/)

# websocket-client

websocket-client is a WebSocket client for Python. It provides access
to low level APIs for WebSockets. websocket-client implements version
[hybi-13](https://tools.ietf.org/html/draft-ietf-hybi-thewebsocketprotocol-13)
of the WebSocket protocol. This client does not currently support the
permessage-deflate extension from
[RFC 7692](https://tools.ietf.org/html/rfc7692).

## Documentation

This project's documentation can be found at
[https://websocket-client.readthedocs.io/](https://websocket-client.readthedocs.io/)

## Contributing

Please see the [contribution guidelines](https://github.com/websocket-client/websocket-client/blob/master/CONTRIBUTING.md)

## Installation

You can use either `python3 setup.py install` or `pip3 install websocket-client`
to install. This module is tested on Python 3.6+.

## Usage Tips

Check out the documentation's FAQ for additional guidelines:
[https://websocket-client.readthedocs.io/en/latest/faq.html](https://websocket-client.readthedocs.io/en/latest/faq.html)

Known issues with this library include lack of WebSocket Compression
support (RFC 7692) and [minimal threading documentation/support](https://websocket-client.readthedocs.io/en/latest/threading.html).

## Performance

The `send` and `validate_utf8` methods can sometimes be bottleneck.
You can disable UTF8 validation in this library (and receive a
performance enhancement) with the `skip_utf8_validation` parameter.
If you want to get better performance, install wsaccel. While
websocket-client does not depend on wsaccel, it will be used if
available. wsaccel doubles the speed of UTF8 validation and
offers a very minor 10% performance boost when masking the
payload data as part of the `send` process. Numpy used to
be a suggested performance enhancement alternative, but
[issue #687](https://github.com/websocket-client/websocket-client/issues/687)
found it didn't help.

## Examples

Many more examples are found in the
[examples documentation](https://websocket-client.readthedocs.io/en/latest/examples.html).

### Long-lived Connection

Most real-world WebSockets situations involve longer-lived connections.
The WebSocketApp `run_forever` loop automatically tries to reconnect when a
connection is lost, and provides a variety of event-based connection controls.

```python
import websocket
import _thread
import time

def on_message(ws, message):
    print(message)

def on_error(ws, error):
    print(error)

def on_close(ws, close_status_code, close_msg):
    print("### closed ###")

def on_open(ws):
    def run(*args):
        for i in range(3):
            time.sleep(1)
            ws.send("Hello %d" % i)
        time.sleep(1)
        ws.close()
        print("thread terminating...")
    _thread.start_new_thread(run, ())

if __name__ == "__main__":
    websocket.enableTrace(True)
    ws = websocket.WebSocketApp("ws://echo.websocket.org/",
                              on_open=on_open,
                              on_message=on_message,
                              on_error=on_error,
                              on_close=on_close)

    ws.run_forever()
```

### Short-lived Connection

This is if you want to communicate a short message and disconnect
immediately when done. For example, if you want to confirm that a WebSocket
server is running and responds properly to a specific request.

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

### Acknowledgements

Thanks to @battlemidget and @ralphbean for helping migrate this project to
Python 3.
