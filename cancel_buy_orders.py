from binance import Client

def cancel(api, secret, bool_test, symbol):
    try:
        client = Client(api, secret, testnet = bool_test)
        orders = client.get_open_orders(symbol=symbol+"USDT")
    except:
        return
    for order in orders:
        if order["side"] == "BUY":
            try:
                client.cancel_order(symbol=symbol+"USDT", orderId=order["orderId"])
            except:
                pass