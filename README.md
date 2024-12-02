[ETHEREUM_MAINNET-TRANSACTIONS-21294932.json](https://github.com/user-attachments/files/17971117/ETHEREUM_MAINNET-TRANSACTIONS-21294932.json)
![incoming-vbytes-all-1732138072](https://github.com/user-attachments/assets/9928ded7-3e88-4cb9-9c8b-2f36365a32da)
[remix-run-remix-2bgp95.zip](https://github.com/user-attachments/files/17971120/remix-run-remix-2bgp95.zip)
[Transaction_Trend_20241124.csv](https://github.com/user-attachments/files/17971119/Transaction_Trend_20241124.csv)


[![docs](https://readthedocs.org/projects/websocket-client/badge/?style=flat)](https://websocket-client.readthedocs.io/)
[![Build Status](https://github.com/websocket-client/websocket-client/actions/workflows/build.yml/badge.svg)](https://github.com/websocket-client/websocket-client/actions/workflows/build.yml)
[![codecov](https://codecov.io/gh/websocket-client/websocket-client/branch/master/graph/badge.svg?token=pcXhUQwiL3)](https://codecov.io/gh/websocket-client/websocket-client)
[![PyPI Downloads](https://pepy.tech/badge/websocket-client)](https://pepy.tech/project/websocket-client)
[![PyPI version](https://img.shields.io/pypi/v/websocket_client)](https://pypi.org/project/websocket_client/)
[![License](https://img.shields.io/badge/License-Apache_2.0-blue.svg)](https://opensource.org/licenses/Apache-2.0)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

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

You can use `pip install websocket-client` to install, or `pip install -e .`
to install from a local copy of the code. This module is tested on Python 3.9+.

There are several optional dependencies that can be installed to enable
specific websocket-client features.
- To install `python-socks` for proxy usage and `wsaccel` for a minor performance boost, use:
 `pip install websocket-client[optional]`
- To install `websockets` to run unit tests using the local echo server, use:
 `pip install websocket-client[test]`
- To install `Sphinx` and `sphinx_rtd_theme` to build project documentation, use:
 `pip install websocket-client[docs]`

While not a strict dependency, [rel](https://github.com/bubbleboy14/registeredeventlistener)
is useful when using `run_forever` with automatic reconnect. Install rel with `pip install rel`.

Footnote: Some shells, such as zsh, require you to escape the `[` and `]` characters with a `\`.

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
The WebSocketApp `run_forever` loop will automatically try to reconnect
to an open WebSocket connection when a network
connection is lost if it is provided with:

- a `dispatcher` argument (async dispatcher like rel or pyevent)
- a non-zero `reconnect` argument (delay between disconnection and attempted reconnection)

`run_forever` provides a variety of event-based connection controls
using callbacks like `on_message` and `on_error`.
`run_forever` **does not automatically reconnect** if the server
closes the WebSocket gracefully (returning
[a standard websocket close code](https://www.rfc-editor.org/rfc/rfc6455.html#section-7.4.1)).
[This is the logic](https://github.com/websocket-client/websocket-client/pull/838#issuecomment-1228454826) behind the decision.
Customizing behavior when the server closes
the WebSocket should be handled in the `on_close` callback.
This example uses [rel](https://github.com/bubbleboy14/registeredeventlistener)
for the dispatcher to provide automatic reconnection.

```python
import websocket
import _thread
import time
import rel

def on_message(ws, message):
    print(message)

def on_error(ws, error):
    print(error)

def on_close(ws, close_status_code, close_msg):
    print("### closed ###")

def on_open(ws):
    print("Opened connection")

if __name__ == "__main__":
    websocket.enableTrace(True)
    ws = websocket.WebSocketApp("wss://api.gemini.com/v1/marketdata/BTCUSD",
                              on_open=on_open,
                              on_message=on_message,
                              on_error=on_error,
                              on_close=on_close)

    ws.run_forever(dispatcher=rel, reconnect=5)  # Set dispatcher to automatic reconnection, 5 second reconnect delay if connection closed unexpectedly
    rel.signal(2, rel.abort)  # Keyboard Interrupt
    rel.dispatch()
```

### Short-lived Connection

This is if you want to communicate a short message and disconnect
immediately when done. For example, if you want to confirm that a WebSocket
server is running and responds properly to a specific request.

```python
from websocket import create_connection

ws = create_connection("ws://echo.websocket.events/")
print(ws.recv())
print("Sending 'Hello, World'...")
ws.send("Hello, World")
print("Sent")
print("Receiving...")
result =  ws.recv()
print("Received '%s'" % result)
ws.close()
```
