import logging, threading, os, time , sys, json, pickle
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
    sell_order_count = 0
    open_buys  = []
    open_sells = []
    ###############################    Helper Functions   ############################################## 
    def make_order(side, price, unit):
        nonlocal open_buys, open_sells   ## if there is a order with same price do not make order
        if side == Client.SIDE_BUY and price in open_buys:
            return None
        if side == Client.SIDE_SELL and price in open_sells:
            return None

        result = None
        try:
            result = client.create_order(symbol = symbol, side=side, 
    type=Client.ORDER_TYPE_LIMIT, quantity=unit, price = price, timeInForce=Client.TIME_IN_FORCE_GTC)
            open_buys.append(price) if side == Client.SIDE_BUY else open_sells.append(price)
        except Exception as e:
            print(e)
            return None
                       
        print(f"ORDER OPENED {result['side']} -> {result['price']}")
        return result

    def bulk_buy():
        nonlocal sell_order_count
        buy = client.create_order(symbol = symbol, side=Client.SIDE_BUY, type=Client.ORDER_TYPE_MARKET, quantity=unit*5)
        price = None
        while not price:
            try:
                price=float(buy["fills"][0]["price"])
            except:
                pass

        print(f"\nBULK BUY")
        print(buy)
        for i in range(1,6):
            sell = make_order(Client.SIDE_SELL, Decimal("%.2f" % (price + step*i)), unit)
        sell_order_count = 5
        return price

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
        nonlocal open_buys, open_sells
        open_buys = []
        open_sells = []
        print("BOT HAS BEEN STARTED")
        price = bulk_buy()
        delete_buy_orders()
        for i in range(1, grids+1):
            buy = make_order(Client.SIDE_BUY, Decimal("%.2f" % (price - step*i)), unit)
    
    # keep ex sell orders in user data
    ex_sell_orders = []
    orders = client.get_open_orders(symbol=symbol)
    for order in orders:
        if order["side"] == "SELL":
            ex_sell_orders.append(order["orderId"])
    
    users = {}
    with open('users_data.pckl', 'rb') as users_data:  
        users = pickle.load(users_data) 
    users[user]["ex_sell_orders"] = ex_sell_orders
    with open('users_data.pckl', 'wb') as users_data:
        pickle.dump(users, users_data)

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
                        sell_order_count -= 1
                        try:
                            open_sells.remove(Decimal("%.2f" % price))
                        except: 
                            pass
                        buy = make_order(Client.SIDE_BUY, Decimal("%.2f" % (price - step)), unit)

                        if findmin_openOrders()[1] > grids:  #eğer gridden fazla buy order var ise en küçüğü iptal et
                            try:
                                canceled = client.cancel_order(symbol=symbol, orderId=findmin_openOrders()[0] )
                                print(f"CANCELED -> {canceled['price']} ")
                                open_buys.remove( Decimal("%.2f" % float(canceled["price"])) )
                            except:
                                pass
                                    
                        if sell_order_count == 0:
                            initialize()
                        increment(user)   ## increment sell_count to calculate reports

                    if stream["S"] == "BUY":
                        print(f"\nBUY -> {price} ")
                        try:
                            open_buys.remove(Decimal("%.2f" % price))
                        except: 
                            pass
                        sell = make_order(Client.SIDE_SELL, Decimal("%.2f" % (price + step)), unit )
                        sell_order_count += 1
                        buy = make_order(Client.SIDE_BUY, Decimal("%.2f" % (price - step*grids)) , unit )

                except Exception as e:
                    print(e)
                    time.sleep(60)
                    client = Client(api, secret)
                    continue                    

            if stream["e"] == "error":
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

