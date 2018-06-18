import websocket
from threading import Thread
import time
import sys


class MyApp(websocket.WebSocketApp):
    def on_message(self, message):
        print(message)

    def on_error(self, error):
        print(error)

    def on_close(self):
        print("### closed ###")

    def on_open(self):
        def run(*args):
            for i in range(3):
                # send the message, then wait
                # so thread doesn't exit and socket
                # isn't closed
                self.send("Hello %d" % i)
                time.sleep(1)

            time.sleep(1)
            self.close()
            print("Thread terminating...")

        Thread(target=run).start()


if __name__ == "__main__":
    websocket.enableTrace(True)
    if len(sys.argv) < 2:
        host = "ws://echo.websocket.org/"
    else:
        host = sys.argv[1]
    ws = MyApp(host)
    ws.run_forever()
