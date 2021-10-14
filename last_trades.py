from binance import Client
from decimal import *
import time, sys
import datetime as dt

def trades(symbol, api, secret):
    trades = []
    client = Client(api, secret)
    curr_trades = client.get_my_trades(symbol=symbol+"USDT", limit=20)
    
    for trade in reversed(curr_trades):
        html_trade = {}
        html_trade["side"]         = "ALIM" if trade["isBuyer"] else "SATIM"
        html_trade["price"]        = "%.2f" % float(trade["price"])
        html_trade["qty"]          = trade["qty"][:5] + " " + symbol
        html_trade["commission"]   = "%.4f" % float(trade["commission"]) + " " + trade["commissionAsset"]
        html_trade["time"]         = str(dt.datetime.fromtimestamp(int(trade["time"])/1000) + dt.timedelta(hours=3) )[:-7]
        trades.append(html_trade)
    return trades
