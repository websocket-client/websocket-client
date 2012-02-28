#!/usr/bin/env python

import argparse
import code
import sys
import threading
import websocket
try:
    import readline
except:
    pass


OPCODE_DATA = (websocket.ABNF.OPCODE_TEXT, websocket.ABNF.OPCODE_BINARY)
ENCODING = getattr(sys.stdin, "encoding", "").lower()


def parse_args():
    parser = argparse.ArgumentParser(description="WebSocket Simple Dump Tool")
    parser.add_argument("url", metavar="ws_url",
                        help="websocket url. ex. ws://echo.websocket.org/")

    return parser.parse_args()


class InteractiveConsole(code.InteractiveConsole):
    def write(self, data):
        sys.stdout.write("\033[2K\033[E")
        # sys.stdout.write("\n")
        sys.stdout.write("\033[34m" + data + "\033[39m")
        sys.stdout.write("\n> ")
        sys.stdout.flush()


    def raw_input(self, prompt):
        line = raw_input(prompt)
        if ENCODING and ENCODING != "utf-8" and not isinstance(line, unicode):
            line = line.decode(ENCODING).encode("utf-8")
        elif isinstance(line, unicode):
            line = encode("utf-8")

        return line


def main():
    args = parse_args()
    console = InteractiveConsole()
    print "Press Ctrl+C to quit"
    ws = websocket.create_connection(args.url)

    def recv():
        frame = ws.recv_frame()
        if not frame:
            raise websocket.WebSocketException("Not a valid frame %s" % frame)
        elif frame.opcode in OPCODE_DATA:
            return (frame.opcode, frame.data)
        elif frame.opcode == websocket.ABNF.OPCODE_CLOSE:
            ws.send_close()
            return (frame.opcode, None)
        elif frame.opcode == websocket.ABNF.OPCODE_PING:
            ws.pong("Hi!")

        return None, None


    def recv_ws():
        while True:
            opcode, data = recv()
            if opcode in OPCODE_DATA:
                console.write("< %s" % data)

    thread = threading.Thread(target=recv_ws)
    thread.daemon = True
    thread.start()

    while True:
        try:
            message = console.raw_input("> ")
            ws.send(message)
        except KeyboardInterrupt:
            return
        except EOFError:
            return


if __name__ == "__main__":
    try:
        main()
    except Exception, e:
        print e
