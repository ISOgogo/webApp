from binance_f import RequestClient
from binance_f.constant.test import *
from binance_f.base.printobject import *
from binance_f.model.constant import *
from decimal import *
import time, sys, datetime

def reports(symbol, api, secret):
    client = RequestClient(api_key=api, secret_key=secret, url='https://fapi.binance.com')
    now = client.get_servertime()
    now_dt = datetime.datetime.fromtimestamp(int(now)/1000)
    start_dt = now_dt - datetime.timedelta(days=1)
    start = datetime.datetime.timestamp(start_dt)*1000
    curr_trades = client.get_account_trades(symbol=symbol+"USDT", startTime=start, endTime=now )

    realized_pnl = 0
    commission = 0
    sell_count = 0
    for trade in curr_trades:
        if trade.side == "SELL":
            sell_count += 1
        realized_pnl += float(trade.realizedPnl)
        commission += float(trade.commission)
    return ("%.2f" % realized_pnl, "%.2f" % commission, sell_count)
