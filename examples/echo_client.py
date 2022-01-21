import websocket

if __name__ == "__main__":
    websocket.enableTrace(True)
    ws = websocket.create_connection("ws://echo.websocket.events/")
    ws.recv()
    print("Sending 'Hello, World'...")
    ws.send("Hello, World")
    print("Sent")
    print("Receiving...")
    result = ws.recv()
    print("Received '%s'" % result)
    ws.close()
