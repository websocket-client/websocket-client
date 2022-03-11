import websocket
import rel

addr = "wss://api.gemini.com/v1/marketdata/%s"

if __name__ == "__main__":
    for symbol in ["BTCUSD", "ETHUSD", "ETHBTC"]:
        ws = websocket.WebSocketApp(addr % (symbol,), on_message=lambda w, m: print(m))
        ws.run_forever(dispatcher=rel)
    rel.signal(2, rel.abort)  # Keyboard Interrupt
    rel.dispatch()
