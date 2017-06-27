import websocket

server = '127.0.0.1'
port = 8087
connected = False


def on_open(ws):
    print("Opening...")
    ws.send('opened')

def on_close(ws):
    print("Close")

def on_message(ws, message):
    print(message)


def on_error(ws, error):
    print("ERROR: {0}".format(error))
    on_close(ws)


ws = websocket.WebSocketApp("ws://{0}:{1}".format(server, port),
                                 on_message=lambda ws, msg: on_message(ws, msg),
                                 on_error=lambda ws, err: on_error(ws, err),
                                 on_close=lambda ws: on_close(ws))
ws.on_open = lambda ws: on_open(ws)
ws.run_forever()
ws = None
