import time
import socket
import inspect
import selectors
import threading
from typing import Any, TYPE_CHECKING, Callable, Optional, Tuple, Union

if TYPE_CHECKING:
    from ._app import WebSocketApp
from ._logging import info
from ._socket import send

"""
_dispatcher.py
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


class DispatcherBase:
    """
    DispatcherBase
    """

    def __init__(
        self, app: "WebSocketApp", ping_timeout: Optional[Union[float, int]]
    ) -> None:
        self.app = app
        self.ping_timeout = ping_timeout
        self._wakeup_lock = threading.Lock()
        self._wakeup: Optional[Tuple[threading.Event, socket.socket]] = None

    def _wake(self) -> None:
        with self._wakeup_lock:
            if self._wakeup is not None:
                stopped, writer = self._wakeup
                stopped.set()
                try:
                    writer.send(b"\0")
                except BlockingIOError:
                    pass  # A pending wakeup already makes the selector readable.

    def _read(
        self, read_callback: Callable, check_callback: Callable, select: Callable
    ) -> None:
        websocket = self.app.sock
        if websocket is None or websocket.sock is None:
            return
        sock = websocket.sock
        reader, writer = socket.socketpair()
        writer.setblocking(False)
        stopped = threading.Event()
        sel = None
        try:
            sel = selectors.DefaultSelector()
            with self._wakeup_lock:
                self._wakeup = (stopped, writer)
            try:
                sel.register(sock, selectors.EVENT_READ)
            except (OSError, ValueError):
                if not self.app.keep_running:
                    return
                raise
            sel.register(reader, selectors.EVENT_READ)
            while self.app.keep_running:
                try:
                    ready = select(sock, sel)
                except (OSError, ValueError):
                    if stopped.is_set() or not self.app.keep_running:
                        break
                    raise
                if stopped.is_set() or not self.app.keep_running:
                    break
                if ready and not read_callback():
                    break
                check_callback()
        finally:
            with self._wakeup_lock:
                if self._wakeup is not None and self._wakeup[1] is writer:
                    self._wakeup = None
            if sel is not None:
                sel.close()
            reader.close()
            writer.close()

    def timeout(self, seconds: Optional[Union[float, int]], callback: Callable) -> None:
        if seconds is not None:
            time.sleep(seconds)
        callback()

    def reconnect(self, seconds: int, reconnector: Callable) -> None:
        try:
            info(
                f"reconnect() - retrying in {seconds} seconds [{len(inspect.stack())} frames in stack]"
            )
            time.sleep(seconds)
            reconnector(reconnecting=True)
        except KeyboardInterrupt as e:
            info(f"User exited {e}")
            raise e

    def send(self, sock: socket.socket, data: Union[str, bytes]) -> int:
        return send(sock, data)


class Dispatcher(DispatcherBase):
    """
    Dispatcher
    """

    def read(
        self,
        sock: socket.socket,
        read_callback: Callable,
        check_callback: Callable,
    ) -> None:
        self._read(
            read_callback,
            check_callback,
            lambda sock, sel: sel.select(self.ping_timeout),
        )


class SSLDispatcher(DispatcherBase):
    """
    SSLDispatcher
    """

    def read(
        self,
        sock: socket.socket,
        read_callback: Callable,
        check_callback: Callable,
    ) -> None:
        self._read(read_callback, check_callback, self.select)

    def select(self, sock: Any, sel: selectors.DefaultSelector) -> Any:
        if self.app.sock is None:
            return None
        if sock is None:
            sock = self.app.sock.sock
        if sock is None:
            return None
        if sock.pending():
            return [
                sock,
            ]

        r = sel.select(self.ping_timeout)

        if len(r) > 0:
            return r[0][0]
        return None


class WrappedDispatcher:
    """
    WrappedDispatcher
    """

    def __init__(
        self,
        app: "WebSocketApp",
        ping_timeout: Optional[Union[float, int]],
        dispatcher: Any,
        handleDisconnect: Optional[Callable],
    ) -> None:
        self.app = app
        self.ping_timeout = ping_timeout
        self.dispatcher = dispatcher
        self.handleDisconnect = handleDisconnect
        dispatcher.signal(2, dispatcher.abort)  # keyboard interrupt

    def read(
        self,
        sock: socket.socket,
        read_callback: Callable,
        check_callback: Callable,
    ) -> None:
        self.dispatcher.read(sock, read_callback)
        if self.ping_timeout:
            self.timeout(self.ping_timeout, check_callback)

    def send(self, sock: socket.socket, data: Union[str, bytes]) -> int:
        self.dispatcher.buffwrite(sock, data, send, self.handleDisconnect)
        return len(data)

    def timeout(self, seconds: float, callback: Callable, *args: Any) -> None:
        self.dispatcher.timeout(seconds, callback, *args)

    def reconnect(self, seconds: int, reconnector: Callable) -> None:
        self.timeout(seconds, reconnector, True)
