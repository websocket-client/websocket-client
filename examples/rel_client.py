import websocket, rel

if __name__ == "__main__":
    rel.safe_read()
    for symbol in ["BTCUSD", "ETHUSD", "ETHBTC"]:
        ws = websocket.WebSocketApp("wss://api.gemini.com/v1/marketdata/%s"%(symbol,),
            on_message = lambda w, m : print(m))
        ws.run_forever(dispatcher=rel)
    rel.signal(2, rel.abort) # Keyboard Interrupt
    rel.dispatch()
