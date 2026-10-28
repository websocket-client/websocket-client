"""
_fakes.py — shared test fakes

websocket - WebSocket client library for Python

Copyright 2026 engn33r

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
"""

import contextlib
import os
import socket
import ssl
import struct
from types import SimpleNamespace
from unittest import mock

from websocket._abnf import ABNF, frame_buffer

__all__ = [
    "SockMock",
    "HeaderSockMock",
    "OptsList",
    "FakeSelector",
    "FakePeer",
    "FakeClock",
    "FakeConn",
    "FakeLoop",
    "RunForeverHarness",
]


class SockMock:
    """Queue-backed fake stream socket: recv() drains queued packets
    (byte strings, or Exceptions to raise), send() records and succeeds."""

    def __init__(self):
        self.data = []
        self.sent = []

    def add_packet(self, data):
        self.data.append(data)

    def gettimeout(self):
        return None

    def recv(self, bufsize):
        if not self.data:
            return b""
        e = self.data.pop(0)
        if isinstance(e, Exception):
            raise e
        if len(e) > bufsize:
            self.data.insert(0, e[bufsize:])
        return e[:bufsize]

    def send(self, data):
        self.sent.append(data)
        return len(data)

    def close(self):
        pass


class HeaderSockMock(SockMock):
    """SockMock preloaded with a recorded response from tests/data."""

    def __init__(self, fname):
        SockMock.__init__(self)
        path = os.path.join(os.path.dirname(__file__), fname)
        with open(path, "rb") as f:
            self.add_packet(f.read())


class OptsList:
    """Minimal options object for _http.connect()."""

    def __init__(self):
        self.timeout = 1
        self.sockopt = []
        self.sslopt = {"cert_reqs": ssl.CERT_NONE}


class FakeSelector:
    """selectors.DefaultSelector stand-in. Records the timeout each
    select() was called with and reports a fixed readiness set."""

    def __init__(self, ready=None):
        self.polled_timeout = None
        self._ready = [] if ready is None else ready

    def register(self, *args, **kwargs):
        pass

    def select(self, timeout):
        self.polled_timeout = timeout
        return self._ready

    def close(self):
        pass


class FakePeer:
    """A real-socket server side over socketpair(). Sends frames with the
    library's own ABNF.format() and parses what the client sends with the
    library's own frame_buffer, so framing bugs surface as test failures."""

    def __init__(self, timeout=1.0):
        self.peer, self.client = socket.socketpair()
        self.peer.settimeout(timeout)
        self.client.settimeout(timeout)
        self.sent = []
        self.received = []
        self._buffer = frame_buffer(self.peer.recv, skip_utf8_validation=True)

    def send_frame(self, opcode, payload=b"", fin=1, rsv1=0):
        frame = ABNF(fin, rsv1, 0, 0, opcode, 0, payload).format()
        self.peer.sendall(frame)
        self.sent.append((opcode, payload))

    def send_raw(self, data):
        self.peer.sendall(data)

    def read_frame(self):
        """Read one masked client frame; returns (opcode, payload)."""
        frame = self._buffer.recv_frame()
        self.received.append((frame.opcode, frame.data))
        return frame.opcode, frame.data

    def close(self):
        self.peer.close()
        self.client.close()


class FakeClock:
    """Deterministic time source: advances only when slept on."""

    def __init__(self, start=1000.0):
        self.now = start
        self.sleeps = []

    def time(self):
        return self.now

    def monotonic(self):
        return self.now

    def sleep(self, seconds):
        self.sleeps.append(seconds)
        self.now += seconds


class FakeConn:
    """Scripted stand-in for websocket._app.WebSocket: hands out frames
    and exceptions from a script, records every call the app makes."""

    def __init__(self, *args, **kwargs):
        self.sock = object()
        self.connected = False
        self.close_frame = None  # read by WebSocketApp.close()
        self.script = []
        self.calls = []
        self.sent = []

    # -- lifecycle ---------------------------------------------------
    def connect(self, *args, **kwargs):
        self.calls.append(("connect", args, kwargs))
        self.connected = True

    def settimeout(self, timeout):
        self.calls.append(("settimeout", timeout))

    def send(self, payload, opcode=ABNF.OPCODE_TEXT):
        self.calls.append(("send", opcode, payload))
        self.sent.append((opcode, payload))

    def close(self, **kwargs):
        self.calls.append(("close", kwargs))
        self.connected = False

    def shutdown(self):
        self.calls.append(("shutdown",))

    # -- scripted reads ----------------------------------------------
    def recv_data_frame(self, *args, **kwargs):
        """Pop the next scripted (opcode, frame) or raise the scripted
        exception. An exhausted script answers with a normal close (1000),
        so a run ends the way a polite peer ends it."""
        if self.script:
            item = self.script.pop(0)
            if isinstance(item, BaseException):
                raise item
        else:
            item = (
                ABNF.OPCODE_CLOSE,
                ABNF.create_frame(struct.pack("!H", 1000), ABNF.OPCODE_CLOSE),
            )
        self.calls.append(("recv_data_frame", item[0]))
        return item


class FakeLoop:
    """External dispatcher with rel's semantics, driven by hand.

    - A read callback stays registered while it returns a truthy value.
    - A timer re-arms while its callback returns a truthy value. Delays are
      recorded, not waited on: each tick fires every armed timer once.
    - Callback exceptions propagate out of tick().
    - abort() stops the loop and drops every registration.
    """

    def __init__(self):
        self.reads = []
        self.timers = []
        self.signals = []
        self.writes = []
        self.aborted = False

    def read(self, sock, callback, *args):
        self.reads.append((sock, callback, args))

    def timeout(self, seconds, callback, *args):
        self.timers.append((seconds, callback, args))

    def signal(self, sig, handler, *args):
        self.signals.append((sig, handler, args))

    def buffwrite(self, sock, data, send_func, disconnect_handler):
        self.writes.append((sock, data, send_func, disconnect_handler))

    def abort(self):
        self.aborted = True
        self.reads = []
        self.timers = []

    def tick(self):
        """One loop iteration: every registered read callback, then every
        armed timer, each once. Returns True while anything is registered."""
        for entry in list(self.reads):
            sock, callback, args = entry
            if not callback(*args) and entry in self.reads:
                self.reads.remove(entry)
        for entry in list(self.timers):
            _, callback, args = entry
            if not callback(*args) and entry in self.timers:
                self.timers.remove(entry)
        return bool(self.reads or self.timers)

    def dispatch(self, max_ticks=100):
        """Tick until nothing is registered or abort() is called. Raises
        AssertionError after max_ticks so a stuck callback fails the test
        instead of hanging it."""
        for _ in range(max_ticks):
            if self.aborted or not self.tick():
                return
        raise AssertionError(f"FakeLoop still busy after {max_ticks} ticks")


class RunForeverHarness:
    """Drives WebSocketApp.run_forever() deterministically:

    - patches websocket._app.WebSocket with a FakeConn subclass whose
      script (frames and exceptions) is set per connection;
    - makes Dispatcher.read synchronous: the read callback runs until it
      returns False;
    - replaces the module clocks with a FakeClock.

    Records the connections, the per-read results and the back-off sleeps.
    Use as a context manager around run_forever().
    """

    def __init__(self, script=()):
        self.clock = FakeClock()
        self.script = list(script)
        self.connections = []
        self.read_results = []
        self._stack = None

    def __enter__(self):
        import websocket._app as app_mod
        import websocket._dispatcher as dispatcher_mod

        harness = self

        class ScriptedConn(FakeConn):
            def __init__(self, *args, **kwargs):
                super().__init__(*args, **kwargs)
                self.script = list(harness.script)
                harness.connections.append(self)

        def sync_read(self, sock, callback, check):
            while True:
                result = callback()
                harness.read_results.append(result)
                if result is False:
                    break
                if check:
                    check()

        # Replace each module's `time` binding, not attributes of the shared
        # `time` module: the fake clock then never leaks into other modules,
        # threads or later tests.
        fake_time = SimpleNamespace(
            time=self.clock.time,
            monotonic=self.clock.monotonic,
            sleep=self.clock.sleep,
        )
        with contextlib.ExitStack() as stack:
            stack.enter_context(mock.patch.object(app_mod, "WebSocket", ScriptedConn))
            stack.enter_context(
                mock.patch.object(dispatcher_mod.Dispatcher, "read", sync_read)
            )
            stack.enter_context(mock.patch.object(app_mod, "time", fake_time))
            stack.enter_context(mock.patch.object(dispatcher_mod, "time", fake_time))
            self._stack = stack.pop_all()
        return self

    def __exit__(self, *exc_info):
        self._stack.close()
        self._stack = None
        return False
