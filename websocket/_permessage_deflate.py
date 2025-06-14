import zlib
from typing import Optional

from ._exceptions import WebSocketProtocolException, WebSocketPayloadException
from ._abnf import ABNF

"""
_core.py
websocket - WebSocket client library for Python

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.

--- 

This code is based on work of the python websockets library
https://github.com/python-websockets/websockets

Copyright Aymeric Augustin and contributors

Licensed under the following BSD-3-Clause License:

Redistribution and use in source and binary forms, with or without
modification, are permitted provided that the following conditions are met:

    * Redistributions of source code must retain the above copyright notice,
      this list of conditions and the following disclaimer.
    * Redistributions in binary form must reproduce the above copyright notice,
      this list of conditions and the following disclaimer in the documentation
      and/or other materials provided with the distribution.
    * Neither the name of the copyright holder nor the names of its contributors
      may be used to endorse or promote products derived from this software
      without specific prior written permission.

THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND
ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE
FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL
DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR
SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER
CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY,
OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
"""

class CompressionOptions:
    def __init__(
            self,
            server_no_context_takeover: bool = False,
            client_no_context_takeover: bool = False,
            server_max_window_bits: int | None = None,
            client_max_window_bits: int | bool | None = 12
    ) -> None:
        # note: isinstance(client_max_window_bits, int) returns True for bool as well
        if type(client_max_window_bits) == int and not 8 <= client_max_window_bits <= 15:
            raise ValueError("client_max_window_bits must be between 8 and 15 or None")
        if server_max_window_bits and not 8 <= server_max_window_bits <= 15:
            raise ValueError("server_max_window_bits must be between 8 and 15 or None")

        self.server_no_context_takeover = server_no_context_takeover
        self.client_no_context_takeover = client_no_context_takeover
        self.server_max_window_bits = server_max_window_bits
        self.client_max_window_bits = client_max_window_bits

    def to_header(self) -> str:
        options = ["permessage-deflate"]

        if self.server_no_context_takeover:
            options.append("server_no_context_takeover")
        if self.client_no_context_takeover:
            options.append("client_no_context_takeover")
        if isinstance(self.server_max_window_bits, int):
            options.append(f"server_max_window_bits={self.server_max_window_bits}")
        if type(self.client_max_window_bits) == int:  # see note in __init__
            options.append(f"client_max_window_bits={self.client_max_window_bits}")
        elif self.client_max_window_bits is not None:
            options.append("client_max_window_bits")

        return "; ".join(options)

    def negotiate(
            self,
            agreed_parameters: "CompressionOptions"
    ) -> "CompressionOptions":
        """
        Negotiate compression options with the server's response and return the final options
        used for the connection.
        """
        # make a copy of the agreed parameters to avoid modifying the original
        agreed_parameters = CompressionOptions(
            server_no_context_takeover=agreed_parameters.server_no_context_takeover,
            client_no_context_takeover=agreed_parameters.client_no_context_takeover,
            server_max_window_bits=agreed_parameters.server_max_window_bits,
            client_max_window_bits=agreed_parameters.client_max_window_bits
        )

        # server_no_context_takeover
        if self.server_no_context_takeover and not agreed_parameters.server_no_context_takeover:
            raise ValueError("Server does not allow context takeover, but we requested it.")

        # client_no_context_takeover
        if self.client_no_context_takeover and not agreed_parameters.client_no_context_takeover:
            # rfc7692 - page 20
            agreed_parameters.client_no_context_takeover = True

        # server_max_window_bits
        # when requested by us, server must set it to the same value or lower
        if self.server_max_window_bits:
            if not agreed_parameters.server_max_window_bits:
                raise ValueError("Server did not provide server_max_window_bits, but we requested it.")
            if agreed_parameters.server_max_window_bits > self.server_max_window_bits:
                raise ValueError(
                    f"Server provided server_max_window_bits={agreed_parameters.server_max_window_bits}, "
                    f"but we requested a lower value of {self.server_max_window_bits}."
                )

        # client_max_window_bits
        # if we did not send any client_max_window_bits, server must not set it either (rfc7692 - page 17)
        if self.client_max_window_bits is None:
            if agreed_parameters.client_max_window_bits is not None:
                raise ValueError("Server provided client_max_window_bits, but we did not specify we support it.")

        # if we sent a client_max_window_bits, server must set it to the same value or lower
        elif type(self.client_max_window_bits) == int:
            if not agreed_parameters.client_max_window_bits:
                # server did not provide client_max_window_bits, we are allowed to use our value
                agreed_parameters.client_max_window_bits = self.client_max_window_bits
            elif agreed_parameters.client_max_window_bits > self.client_max_window_bits:
                raise ValueError(
                    f"Server provided client_max_window_bits={agreed_parameters.client_max_window_bits}, "
                    f"but we requested a lower value of {self.client_max_window_bits}."
                )

        # if left unspecified by the negotiation, set defaults
        agreed_parameters.client_max_window_bits = agreed_parameters.client_max_window_bits or 15
        agreed_parameters.server_max_window_bits = agreed_parameters.server_max_window_bits or 15
        return agreed_parameters

    @classmethod
    def from_header(cls, header: str) -> "CompressionOptions":
        """
        Create a CompressionOptions instance from the header string.
        """

        options = header.lower().split(";")
        server_no_context_takeover = False
        client_no_context_takeover = False
        server_max_window_bits = None
        client_max_window_bits = None

        for option in options:
            option = option.strip()

            if option == "server_no_context_takeover":
                server_no_context_takeover = True
            elif option == "client_no_context_takeover":
                client_no_context_takeover = True
            elif option.startswith("server_max_window_bits"):
                server_max_window_bits = int(option.split("=")[1])
            elif option.startswith("client_max_window_bits"):
                client_max_window_bits = int(option.split("=")[1]) if "=" in option else True

        return cls(
            server_no_context_takeover=server_no_context_takeover,
            client_no_context_takeover=client_no_context_takeover,
            server_max_window_bits=server_max_window_bits,
            client_max_window_bits=client_max_window_bits
        )


class CompressionExtension:
    _empty_uncompressed_block = b"\x00\x00\xff\xff"
    _not_compressed_optcodes = (
        ABNF.OPCODE_CLOSE,
        ABNF.OPCODE_PING,
        ABNF.OPCODE_PONG
    )

    compressor: Optional[zlib.compressobj] = None
    decompressor: Optional[zlib.decompressobj] = None

    def __init__(
            self,
            negotiated_options: CompressionOptions
    ):
        self.options = negotiated_options
        self._initial_frame_compressed = False
        self._reset_decompressor()
        self._reset_compressor()

    def _reset_decompressor(self):
        if self.decompressor:
            del self.decompressor
        self.decompressor = zlib.decompressobj(wbits=-self.options.server_max_window_bits)

    def _reset_compressor(self):
        if self.compressor:
            del self.compressor
        self.compressor = zlib.compressobj(wbits=-self.options.client_max_window_bits)

    def compress(self, abnf: ABNF) -> ABNF:
        # Skip control frames.
        if abnf.opcode in self._not_compressed_optcodes:
            return abnf

        # reset compressor for each new message if client_no_context_takeover is set
        if abnf.opcode != ABNF.OPCODE_CONT and self.options.client_no_context_takeover:
            self._reset_compressor()

        # Compress data.
        data = self.compressor.compress(abnf.data) + self.compressor.flush(zlib.Z_SYNC_FLUSH)
        if abnf.fin:
            # Sync flush generates between 5 or 6 bytes, ending with the bytes
            # 0x00 0x00 0xff 0xff, which must be removed.
            assert data[-4:] == self._empty_uncompressed_block
            # Making a copy is faster than memoryview(a)[:-4] until 2kB.
            if len(data) < 2048:
                data = data[:-4]
            else:
                data = memoryview(data)[:-4]

        return ABNF(
            abnf.fin,
            abnf.opcode != ABNF.OPCODE_CONT,
            abnf.rsv2,
            abnf.rsv3,
            abnf.opcode,
            abnf.mask_value,
            data
        )

    def decompress(
            self,
            abnf: ABNF,
            *,
            max_size: int | None = None,
    ) -> ABNF:
        """
        Decode an incoming frame.

        """
        # Skip control frames.
        if abnf.opcode in self._not_compressed_optcodes:
            return abnf

        # Handle continuation data frames:
        # - skip if the message isn't encoded
        # - reset "decode continuation data" flag if it's a final frame
        if abnf.opcode == ABNF.OPCODE_CONT:
            if not self._initial_frame_compressed:
                return abnf
            if abnf.fin:
                self._initial_frame_compressed = False

        # Handle text and binary data frames:
        # - skip if the message isn't encoded
        # - unset the rsv1 flag on the first frame of a compressed message
        # - set "decode continuation data" flag if it's a non-final frame
        else:
            if not abnf.rsv1:
                return abnf
            if not abnf.fin:
                self._initial_frame_compressed = True

            # Re-initialize per-message decoder.
            if self.options.server_no_context_takeover:
                self._reset_decompressor()

        # Uncompress data. Protect against zip bombs by preventing zlib from
        # decompressing more than max_length bytes (except when the limit is
        # disabled with max_size = None).
        if abnf.fin and len(abnf.data) < 2044:
            # Profiling shows that appending four bytes, which makes a copy, is
            # faster than calling decompress() again when data is less than 2kB.
            data = bytes(abnf.data) + self._empty_uncompressed_block
        else:
            data = abnf.data
        max_length = 0 if max_size is None else max_size
        try:
            data = self.decompressor.decompress(data, max_length)
            if self.decompressor.unconsumed_tail:
                assert max_size is not None  # help mypy
                raise WebSocketPayloadException(f"decompression produced more than {max_size} bytes of data")
            if abnf.fin and len(abnf.data) >= 2044:
                # This cannot generate additional data.
                self.decompressor.decompress(self._empty_uncompressed_block)
        except zlib.error as exc:
            raise WebSocketProtocolException("decompression failed") from exc

        return ABNF(
            abnf.fin,
            0,
            abnf.rsv2,
            abnf.rsv3,
            abnf.opcode,
            abnf.mask_value,
            data
        )
