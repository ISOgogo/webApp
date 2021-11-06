from binance import Client
from decimal import *
import time, sys, datetime

def open_orders(symbol, api, secret, bool_test, step, ex_sell_orders=[], bulk_buy_orders={}):
    client = Client(api, secret, testnet = bool_test)
    orders = client.get_open_orders(symbol=symbol+"USDT")
    quantity = 0.0
    total_price = 0.0
    count = 0.0
    
    for order in orders:
        if order["side"] == "SELL" and order["orderId"] not in ex_sell_orders:
            
            buy_qty = float(order["origQty"]) - float(order["executedQty"])     #Sell order olduğu için original sizedan executed çıkarınca bize alım yapılan qty kalır
            quantity += buy_qty
            proportion = buy_qty / float(order["origQty"])                      #SELL order hiç dolmamışsa 1e eşit olur kırık ise 1den küçük
            count += proportion
            
            if bulk_buy_orders.get(order["orderId"]):                  
                total_price += bulk_buy_orders.get(order["orderId"]) * proportion
            else:
                total_price += (float(order["price"]) - step) * proportion

    return ("%.3f" % quantity, "%.2f" % (total_price/count) )