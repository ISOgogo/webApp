from binance import Client
from decimal import *
import time, sys, datetime

def reports(symbol, api, secret):
    client = Client(api, secret, testnet=True)
    now = client.get_server_time()["serverTime"]
    now_dt = datetime.datetime.fromtimestamp(int(now)/1000)
    start_dt = now_dt - datetime.timedelta(days=7)
    start = datetime.datetime.timestamp(start_dt)*1000
    
    curr_trades = client.get_my_trades(symbol=symbol+"USDT", startTime=int(start), endTime=int(now)  )

    commission = 0
    sell_count = 0
    for trade in curr_trades:
        if not trade["isBuyer"]:
            sell_count += 1
        commission += float(trade["commission"])
    return ("%.4f" % commission, sell_count)
