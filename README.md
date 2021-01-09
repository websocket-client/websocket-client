# websocket-client

websocket-client module is WebSocket client for python. This provide the
low level APIs for WebSocket. All APIs are the synchronous functions.

websocket-client supports only hybi-13.


## License

- LGPL


## Installation

This module is tested on Python 2.7 and Python 3.x.

Type "python setup.py install" or "pip install websocket-client" to
install.

### Caution

from v0.16.0, we can install by "pip install websocket-client" for
python 3.


This module depend on

- six
- backports.ssl\_match\_hostname for Python 2.x
 
 ### performance
 
"send" method is too slow on pure python. If you want to get better performance, please install wsaccel.
In the future, you could use numpy, but it is sitll working in progress.



## How about Python 3

Now, we support python 3 on single source code from version 0.14.0.
Thanks, @battlemidget and @ralphbean.



## HTTP Proxy

Support websocket access via http proxy. The proxy server must allow
"CONNECT" method to websocket port. Default squid setting is "ALLOWED TO
CONNECT ONLY HTTPS PORT".

Current implementation of websocket-client is using "CONNECT" method via
proxy.

example

``` sourceCode python
import websocket
ws = websocket.WebSocket()
ws.connect("ws://example.com/websocket", http_proxy_host="proxy_host_name", http_proxy_port=3128)
:
```


## Examples

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

``` sourceCode python
from websocket import create_connection
ws = create_connection("ws://echo.websocket.org/")
print("Sending 'Hello, World'...")
ws.send("Hell
```

