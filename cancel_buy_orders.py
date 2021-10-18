from binance import Client

def cancel(api, secret, symbol):
    try:
        client = Client(api, secret)
        orders = client.get_open_orders(symbol=symbol+"USDT")
    except:
        return
    for order in orders:
        if order["side"] == "BUY":
            try:
                client.cancel_order(symbol=symbol+"USDT", orderId=order["orderId"])
            except:
                pass