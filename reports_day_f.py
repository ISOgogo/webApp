from binance_f import RequestClient
from decimal import *
import time, sys, datetime

def reports(symbol, api, secret, bool_test, unit, step, bot_start_time ):
    
    if bool_test:
        client = RequestClient(api_key=api, secret_key=secret, url="https://testnet.binancefuture.com")
    else:
        client = RequestClient(api_key=api, secret_key=secret, url='https://fapi.binance.com')
    
    now = client.get_servertime()
    now_dt = datetime.datetime.fromtimestamp(int(now)/1000)
    start_dt = now_dt - datetime.timedelta(days=1)
    start_dt = bot_start_time if bot_start_time > start_dt else start_dt
    start = datetime.datetime.timestamp(start_dt)*1000
    curr_trades = client.get_account_trades(symbol=symbol+"USDT", startTime=int(start), endTime=int(now))

    profit = 0
    sell_count = 0

    for trade in curr_trades:
        if trade.side == "SELL":
            profit += step*float(trade.qty)
            sell_count += float(trade.qty) / unit

    return ("%.1f" % sell_count, "%.2f" % profit)
