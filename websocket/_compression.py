"""
_compression.py
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

import sys
import zlib
from typing import Optional, Union

from ._exceptions import (
    WebSocketException,
    WebSocketPayloadException,
    WebSocketProtocolException,
)

__all__ = ["PerMessageDeflate"]

EXTENSION_NAME = "permessage-deflate"

# Largest size a compressed message may decompress to unless configured otherwise.
DEFAULT_MAX_MESSAGE_SIZE = 16 * 1024 * 1024

_EMPTY_BLOCK_TAIL = b"\x00\x00\xff\xff"
_MIN_WINDOW_BITS = 8
# zlib cannot compress with an 8 bit window, so the client's own window is 9 to 15.
_MIN_CLIENT_WINDOW_BITS = 9
_MAX_WINDOW_BITS = 15
_WINDOW_SIZE = 1 << _MAX_WINDOW_BITS


class PerMessageDeflate:
    """
    Settings for the permessage-deflate extension (RFC 7692).

    Pass an instance, or ``True`` for the defaults, as the ``compression``
    option of ``WebSocket.connect``, ``create_connection`` or ``WebSocketApp``.
    The extension is offered in the handshake; if the server accepts it,
    messages sent with ``send`` are compressed and compressed messages
    received are decompressed. If the server declines, the connection is
    uncompressed.

    Parameters
    ----------
    client_no_context_takeover: bool
        Compress each sent message on its own and ask the server to expect that.
    server_no_context_takeover: bool
        Ask the server to compress each message it sends on its own.
    client_max_window_bits: bool or int
        True offers the parameter without a value, which lets the server limit
        the window this client compresses with. An int from 9 to 15 also caps it.
        False leaves the parameter out.
    server_max_window_bits: int
        Ask the server to compress with a window of at most 2**value bytes (8 to 15).
    compress_level: int
        zlib compression level for sent messages, -1 (zlib's default) to 9.
    max_message_size: int
        Largest size in bytes a received compressed message may decompress to;
        a larger one raises WebSocketPayloadException. None for no limit.
    """

    def __init__(
        self,
        client_no_context_takeover: bool = False,
        server_no_context_takeover: bool = False,
        client_max_window_bits: Union[bool, int] = True,
        server_max_window_bits: Optional[int] = None,
        compress_level: int = -1,
        max_message_size: Optional[int] = DEFAULT_MAX_MESSAGE_SIZE,
    ) -> None:
        if not isinstance(client_max_window_bits, bool) and not (
            _MIN_CLIENT_WINDOW_BITS <= client_max_window_bits <= _MAX_WINDOW_BITS
        ):
            raise ValueError(
                f"client_max_window_bits must be a bool or {_MIN_CLIENT_WINDOW_BITS} to {_MAX_WINDOW_BITS}"
            )
        if server_max_window_bits is not None and not (
            _MIN_WINDOW_BITS <= server_max_window_bits <= _MAX_WINDOW_BITS
        ):
            raise ValueError(
                f"server_max_window_bits must be {_MIN_WINDOW_BITS} to {_MAX_WINDOW_BITS}"
            )
        if not -1 <= compress_level <= 9:
            raise ValueError("compress_level must be -1 to 9")
        if max_message_size is not None and (
            not isinstance(max_message_size, int)
            or isinstance(max_message_size, bool)
            or max_message_size < 0
        ):
            raise ValueError("max_message_size must be None or an int of at least 0")
        self.client_no_context_takeover = client_no_context_takeover
        self.server_no_context_takeover = server_no_context_takeover
        self.client_max_window_bits = client_max_window_bits
        self.server_max_window_bits = server_max_window_bits
        self.compress_level = compress_level
        self.max_message_size = max_message_size

    def offer(self) -> str:
        """The Sec-WebSocket-Extensions value offering this configuration."""
        params = [EXTENSION_NAME]
        if self.client_no_context_takeover:
            params.append("client_no_context_takeover")
        if self.server_no_context_takeover:
            params.append("server_no_context_takeover")
        if self.client_max_window_bits is True:
            params.append("client_max_window_bits")
        elif self.client_max_window_bits is not False:
            params.append(f"client_max_window_bits={self.client_max_window_bits}")
        if self.server_max_window_bits is not None:
            params.append(f"server_max_window_bits={self.server_max_window_bits}")
        return "; ".join(params)

    def accept(self, response: Optional[str]) -> Optional["deflate_session"]:
        """
        Read the server's Sec-WebSocket-Extensions response to this offer.

        Returns None when the server declined the extension, otherwise the
        session for the connection. Raises WebSocketException when the
        response must fail the connection (RFC 7692 section 7).
        """
        if response is None or not response.strip():
            return None
        extensions = response.split(",")
        if len(extensions) != 1:
            raise WebSocketException(
                f"Server accepted more than one extension: {response!r}"
            )
        name, *raw_params = [p.strip() for p in extensions[0].split(";")]
        if name.lower() != EXTENSION_NAME:
            raise WebSocketException(
                f"Server accepted an unoffered extension: {name!r}"
            )

        params: dict[str, Optional[str]] = {}
        for raw in raw_params:
            key, sep, value = raw.partition("=")
            key = key.strip().lower()
            if key in params:
                raise WebSocketException(f"Duplicate extension parameter: {key!r}")
            params[key] = _unquote(value.strip()) if sep else None

        server_no_context_takeover = False
        client_no_context_takeover = self.client_no_context_takeover
        client_window_bits = (
            _MAX_WINDOW_BITS
            if isinstance(self.client_max_window_bits, bool)
            else self.client_max_window_bits
        )
        for key, value in params.items():
            if key == "server_no_context_takeover":
                _require_no_value(key, value)
                server_no_context_takeover = True
            elif key == "client_no_context_takeover":
                _require_no_value(key, value)
                client_no_context_takeover = True
            elif key == "server_max_window_bits":
                bits = _window_bits(key, value)
                if (
                    self.server_max_window_bits is not None
                    and bits > self.server_max_window_bits
                ):
                    raise WebSocketException(
                        f"server_max_window_bits={bits} exceeds the offered {self.server_max_window_bits}"
                    )
            elif key == "client_max_window_bits":
                if self.client_max_window_bits is False:
                    raise WebSocketException(
                        "Server sent client_max_window_bits, which was not offered"
                    )
                client_window_bits = min(client_window_bits, _window_bits(key, value))
            else:
                raise WebSocketException(f"Unknown extension parameter: {key!r}")

        # A server accepts these requests by echoing them (RFC 7692 section 7.1).
        if self.server_no_context_takeover and not server_no_context_takeover:
            raise WebSocketException("Server did not accept server_no_context_takeover")
        if (
            self.server_max_window_bits is not None
            and "server_max_window_bits" not in params
        ):
            raise WebSocketException("Server did not accept server_max_window_bits")

        return deflate_session(
            server_no_context_takeover=server_no_context_takeover,
            client_no_context_takeover=client_no_context_takeover,
            client_window_bits=client_window_bits,
            compress_level=self.compress_level,
            max_message_size=self.max_message_size,
        )


def _unquote(value: str) -> str:
    if len(value) >= 2 and value[0] == value[-1] == '"':
        return value[1:-1]
    return value


def _require_no_value(key: str, value: Optional[str]) -> None:
    if value is not None:
        raise WebSocketException(f"Extension parameter {key!r} takes no value")


def _window_bits(key: str, value: Optional[str]) -> int:
    if (
        value is None
        or not value.isdigit()
        or value.startswith("0")
        or not _MIN_WINDOW_BITS <= int(value) <= _MAX_WINDOW_BITS
    ):
        raise WebSocketException(f"Invalid value for {key!r}: {value!r}")
    return int(value)


class deflate_session:
    """
    The negotiated permessage-deflate state of one connection.

    ``compress`` must be called in the order messages are written to the
    socket, and ``decompress`` in the order frames are read. When the server
    limits the client to an 8 bit window, which zlib cannot compress with,
    ``compresses`` is False and messages are sent uncompressed.
    """

    def __init__(
        self,
        server_no_context_takeover: bool,
        client_no_context_takeover: bool,
        client_window_bits: int,
        compress_level: int,
        max_message_size: Optional[int],
    ) -> None:
        self.server_no_context_takeover = server_no_context_takeover
        self.client_no_context_takeover = client_no_context_takeover
        self.client_window_bits = client_window_bits
        self.compress_level = compress_level
        self.max_message_size = max_message_size
        self.compresses = client_window_bits >= _MIN_CLIENT_WINDOW_BITS
        if self.compresses:
            self._compressor = self._new_compressor()
        # The last window of decompressed output, which the server may refer
        # back to after it ends a DEFLATE stream with a final block.
        self._history = b""
        self._decompressor = self._new_decompressor()
        self._receiving_compressed = False
        self._received_size = 0

    def _new_compressor(self) -> "zlib._Compress":
        return zlib.compressobj(
            self.compress_level, zlib.DEFLATED, -self.client_window_bits
        )

    def _new_decompressor(self) -> "zlib._Decompress":
        # A full window reads data compressed with any smaller one (RFC 7692 section 7.2.2).
        return zlib.decompressobj(-_MAX_WINDOW_BITS, zdict=self._history)

    def compress(self, data: bytes) -> bytes:
        """Compress one whole message (RFC 7692 section 7.2.1)."""
        if self.client_no_context_takeover:
            self._compressor = self._new_compressor()
        compressed = self._compressor.compress(data) + self._compressor.flush(
            zlib.Z_SYNC_FLUSH
        )
        if compressed.endswith(_EMPTY_BLOCK_TAIL):
            compressed = compressed[: -len(_EMPTY_BLOCK_TAIL)]
        return compressed

    def start_message(self, compressed: bool) -> None:
        """Note the first frame of a received message, whose RSV1 says if it is compressed."""
        self._receiving_compressed = compressed
        self._received_size = 0

    def decompress(self, data: bytes, fin: bool) -> bytes:
        """Decompress one frame of the current received message, if it is compressed."""
        if not self._receiving_compressed:
            return data
        try:
            result = self._inflate(data)
            # A message may go on after a block with BFINAL set (RFC 7692 section 7.2.1).
            while self._decompressor.eof and self._decompressor.unused_data:
                rest = self._decompressor.unused_data
                self._decompressor = self._new_decompressor()
                result += self._inflate(rest)
            # The tail ends the sender's last block, so a stream ended by BFINAL takes none.
            if fin and not self._decompressor.eof:
                result += self._inflate(_EMPTY_BLOCK_TAIL)
        except Exception:
            self._history = b""
            self._decompressor = self._new_decompressor()
            self._receiving_compressed = False
            raise
        if fin and self.server_no_context_takeover:
            self._history = b""
            self._decompressor = self._new_decompressor()
        elif fin and self._decompressor.eof:
            self._decompressor = self._new_decompressor()
        return result

    def _inflate(self, data: bytes) -> bytes:
        limit = self.max_message_size
        # A max_length of 0 tells zlib to decompress without a limit.
        max_length = (
            0 if limit is None else min(limit - self._received_size + 1, sys.maxsize)
        )
        try:
            result = self._decompressor.decompress(data, max_length)
        except zlib.error as e:
            raise WebSocketProtocolException(f"Invalid compressed data: {e}") from e
        self._received_size += len(result)
        if limit is not None and (
            self._received_size > limit or self._decompressor.unconsumed_tail
        ):
            raise WebSocketPayloadException(
                f"Decompressed message exceeds max_message_size ({limit} bytes)"
            )
        if len(result) >= _WINDOW_SIZE:
            self._history = result[-_WINDOW_SIZE:]
        else:
            self._history = (self._history + result)[-_WINDOW_SIZE:]
        return result
