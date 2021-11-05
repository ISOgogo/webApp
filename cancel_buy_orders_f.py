from binance_f import RequestClient

def cancel(api, secret, bool_test, symbol):
    try:
        if bool_test:
            client = RequestClient(api_key=api, secret_key=secret, url="https://testnet.binancefuture.com")
        else:
            client = RequestClient(api_key=api, secret_key=secret, url='https://fapi.binance.com')
        orders = client.get_open_orders(symbol=symbol+"USDT")
    except:
        return

    for order in orders:
        if order.side == "BUY":
            try:
                client.cancel_order(symbol=symbol+"USDT", orderId=order.orderId)
            except:
                pass