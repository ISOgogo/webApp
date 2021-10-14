from binance import Client
from decimal import *
import time, sys, datetime

def reports(symbol, api, secret, step):
    client = Client(api, secret)
    now = int(client.get_server_time()["serverTime"])
    now_dt = datetime.datetime.fromtimestamp(now/1000)
    profit = 0    
    commission = 0
    sell_count = 0
    for i in range(7):
        start_dt = now_dt - datetime.timedelta(days=1)
   
        start = int(datetime.datetime.timestamp(start_dt)*1000)
        curr_trades = client.get_my_trades(symbol=symbol+"USDT", startTime=start, endTime=now)
        
        for trade in curr_trades:
            if not trade["isBuyer"]:
                profit += step*float(trade["qty"])
                sell_count += 1
            commission += float(trade["commission"])
        now = start
    return ("%.3f" % profit, "%.4f" % commission, sell_count)
