from binance import Client
from decimal import *
import time, sys, datetime

def open_orders(symbol, api, secret, step, ex_sell_orders=[]):
    client = Client(api, secret)
    orders = client.get_open_orders(symbol=symbol+"USDT")
    quantity = 0.0
    total_price = 0.0
    count = 0
    for order in orders:
        if order["side"] == "SELL" and order["orderId"] not in ex_sell_orders:
            count += 1
            total_price += float(order["price"])
            quantity += float(order["origQty"]) - float(order["executedQty"])
    return ("%.3f" % quantity, "%.2f" % (total_price/count - step) )