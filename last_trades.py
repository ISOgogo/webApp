from binance_f import RequestClient
from binance_f.constant.test import *
from binance_f.base.printobject import *
from binance_f.model.constant import *
from decimal import *
import time, sys
import datetime as dt

def trades(symbol, api, secret):
    trades = []
    client = RequestClient(api_key=api, secret_key=secret, url='https://fapi.binance.com')
    curr_trades = client.get_account_trades(symbol=symbol+"USDT", limit=20)
    
    for trade in reversed(curr_trades):
        html_trade = {}
        html_trade["side"]         = "ALIM" if trade.side == "BUY" else "SATIM"
        html_trade["price"]        = "%.2f" % trade.price
        html_trade["qty"]          = str(trade.qty) + " " + symbol
        html_trade["commission"]   = "%.2f" % trade.commission + " " + trade.commissionAsset
        html_trade["time"]         = str(dt.datetime.fromtimestamp(int(trade.time)/1000) + dt.timedelta(hours=3) )[:-7]
        trades.append(html_trade)
    return trades
