"""
websocket - WebSocket client library for Python

Copyright (C) 2010 Hiroki Ohtani(liris)

    This library is free software; you can redistribute it and/or
    modify it under the terms of the GNU Lesser General Public
    License as published by the Free Software Foundation; either
    version 2.1 of the License, or (at your option) any later version.

    This library is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
    Lesser General Public License for more details.

    You should have received a copy of the GNU Lesser General Public
    License along with this library; if not, write to the Free Software
    Foundation, Inc., 51 Franklin Street, Fifth Floor,
    Boston, MA  02110-1335  USA

"""

import logging

_logger = logging.getLogger()
_traceEnabled = False

__all__ = ["enableTrace", "dump", "error", "debug", "trace",
           "isEnableForError", "isEnableForDebug"]


def enableTrace(tracable):
    """
    turn on/off the tracability.

    tracable: boolean value. if set True, tracability is enabled.
    """
    global _traceEnabled
    _traceEnabled = tracable
    if tracable:
        if not _logger.handlers:
            _logger.addHandler(logging.StreamHandler())
        _logger.setLevel(logging.DEBUG)


def dump(title, message):
    if _traceEnabled:
        _logger.debug("--- " + title + " ---")
        _logger.debug(message)
        _logger.debug("-----------------------")


def error(msg):
    _logger.error(msg)


def debug(msg):
    _logger.debug(msg)


def trace(msg):
    if _traceEnabled:
        _logger.debug(msg)


def isEnableForError():
    return _logger.isEnabledFor(logging.ERROR)


def isEnableForDebug():
    return _logger.isEnabledFor(logging.DEBUG)
