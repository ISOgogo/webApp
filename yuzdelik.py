import logging, threading, os, time , sys, json
from binance import Client
from decimal import *
from unicorn_binance_websocket_api.unicorn_binance_websocket_api_manager import BinanceWebSocketApiManager
from increment import increment

def argument_converter(fn):
    def wrapper(symbol, step, unit, grids, api, secret, user):
        return fn(symbol, float(step), float(unit), int(grids), api ,secret, user)
    return wrapper

@argument_converter
def bot(symbol, step, unit, grids, api, secret, user):
    
    client = Client(api, secret)
    binance_com_websocket_api_manager = BinanceWebSocketApiManager(exchange="binance.com")
    binance_com_websocket_api_manager.create_stream('arr', '!userData', api_key=api, api_secret=secret)
    logging.basicConfig(level=logging.INFO,
                    filename=os.path.basename(__file__) + '.log',
                    format="{asctime} [{levelname:8}] {process} {thread} {module}: {message}",
                    style="{")
    
    symbol = symbol.upper() + "USDT"
    
    ###############################    Helper Functions   ############################################## 
    def make_order(side, price, unit):
        result = None
        c = 0
        while not result and c<10:
            c+=1
            try:
                result = client.create_order(symbol = symbol, side=side, 
        type=Client.ORDER_TYPE_LIMIT, quantity=unit, price = price, timeInForce=Client.TIME_IN_FORCE_GTC)
            except Exception as e:
                print(e)
                pass
            time.sleep(0.1)

        print(f"ORDER OPENED {result['side']} -> {result['price']}")
        return result

    def bulk_buy():
        buy = client.create_order(symbol = symbol, side=Client.SIDE_BUY, type=Client.ORDER_TYPE_MARKET, quantity=unit*5)
        curr_price=None
        while not curr_price:
            try:
                curr_price = float(buy["fills"][0]["price"])
            except:
                pass

        print(f"\nBULK BUY")
        print(buy)
    
        for i in range(1,6):
            curr_price = curr_price*(100+step)/100
            sell = make_order(Client.SIDE_SELL, Decimal("%.2f" % curr_price), unit)
        return curr_price

    def findmin_openOrders():
        orders = client.get_open_orders(symbol=symbol)
        price = 9999999
        orderId = None
        count = 0
        for order in orders:
            if order["side"] == "BUY":
                count += 1
                if float(order["price"]) < price:
                    price = float(order["price"])
                    orderId = order["orderId"]
        return (orderId, count)
    
    def delete_buy_orders():
        orders = client.get_open_orders(symbol=symbol)
        for order in orders:
            if order["side"] == "BUY":
                try:
                    client.cancel_order(symbol=symbol, orderId=order["orderId"])
                except:
                    pass

    def initialize():
        print("BOT HAS BEEN STARTED")
        curr_price = bulk_buy()
        delete_buy_orders()
        for i in range(1, grids+1):
            curr_price = curr_price*100/(100+step)
            buy = make_order(Client.SIDE_BUY, Decimal("%.2f" % curr_price), unit)

    ex_sell_orders = []
    orders = client.get_open_orders(symbol=symbol)
    for order in orders:
        if order["side"] == "SELL":
            ex_sell_orders.append(order["orderId"])          
    #################################################################################################
    
    initialize()

    while True:
        oldest_stream_data_from_stream_buffer = binance_com_websocket_api_manager.pop_stream_data_from_stream_buffer()
        
        if oldest_stream_data_from_stream_buffer:
            stream = json.loads(oldest_stream_data_from_stream_buffer)
                        
            if stream["e"] == "executionReport" and stream["o"] == "LIMIT" and stream["s"] == symbol and stream["X"] == "FILLED":
                price = float(stream["p"])
                try:
                    if stream["S"] == "SELL" and stream["i"] not in ex_sell_orders:
                        print(f"\nSELL -> {price}")
                        buy = make_order(Client.SIDE_BUY, Decimal("%.2f" % (price*100/(100+step))), unit )               

                        if findmin_openOrders()[1] > grids:  #eğer gridden fazla buy order var ise en küçüğü iptal et
                            deleted = None
                            for i in range(10):
                                try:
                                    deleted = client.cancel_order(symbol=symbol, orderId=findmin_openOrders()[0] )
                                except:
                                    pass
                                if deleted:
                                    break
                        if float(client.get_asset_balance(asset=symbol[:-4])["locked"]) < unit:
                            bulk_buy(price)
                        increment(user)                 
                    if stream["S"] == "BUY":
                        print(f"\nBUY -> {price}")

                        sell = make_order(Client.SIDE_SELL, Decimal("%.2f" % (price*(100+step)/100) ), unit )
            
                        curr_price = price
                        for i in range(grids):
                            curr_price = curr_price/(100+step)*100
                        buy = make_order(Client.SIDE_BUY, Decimal("%.2f" % curr_price ) , unit )
            
                except Exception as e:
                    print(e)
                    time.sleep(60)
                    client = Client(api, secret)
                    continue
            
            elif stream["e"] == "error":
                print(stream)
            
        else:
            time.sleep(0.5)

if __name__ == "__main__":
    a =     sys.argv[1]
    b =     float(sys.argv[2])
    c =     float(sys.argv[3])
    d =     int(sys.argv[4])
    api =   sys.argv[5]
    secret= sys.argv[6]
    user =  sys.argv[7]
    bot(a, b, c, d, api, secret, user)

