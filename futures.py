import logging, threading, os, time , sys, json, pickle
from binance_f import RequestClient
from binance_f.model.constant import *
from decimal import *
from unicorn_binance_websocket_api.unicorn_binance_websocket_api_manager import BinanceWebSocketApiManager

def argument_converter(fn):
    def wrapper(symbol, step, unit, grids, leverage, api, secret, bool_test, user ):
        return fn(symbol, float(step), float(unit), int(grids), int(leverage), api ,secret, bool_test, user)
    return wrapper

@argument_converter
def bot(symbol, step, unit, grids, leverage, api, secret, bool_test, user ):
    
    if bool_test:
        client = RequestClient(api_key=api, secret_key=secret, url="https://testnet.binancefuture.com")
        binance_com_websocket_api_manager = BinanceWebSocketApiManager(exchange="binance.com-futures-testnet")
    else:
        client = RequestClient(api_key=api, secret_key=secret, url='https://fapi.binance.com')
        binance_com_websocket_api_manager = BinanceWebSocketApiManager(exchange="binance.com-futures")

    binance_com_websocket_api_manager.create_stream('arr', '!userData', api_key=api, api_secret=secret)
    logging.basicConfig(level=logging.INFO,
                    filename=os.path.basename(__file__) + '.log',
                    format="{asctime} [{levelname:8}] {process} {thread} {module}: {message}",
                    style="{")
    
    symbol = symbol.upper() + "USDT"
    sell_order_count = 0
    open_buys  = []
    open_sells = []
    
    try:
        client.change_margin_type(symbol=symbol, marginType=FuturesMarginType.ISOLATED)
    except:
        pass
    
    client.change_initial_leverage(symbol=symbol, leverage = leverage)

    ###############################    Helper Functions   ############################################## 
    def increment():
        users = {}
        with open('/var/www/webApp/users_data.pckl', 'rb') as users_data:  
            users = pickle.load(users_data) 
        users[user]["f_sell_count"] += 1
        with open('/var/www/webApp/users_data.pckl', 'wb') as users_data:
            pickle.dump(users, users_data)

    def commission(commission):
        users = {}
        with open('/var/www/webApp/users_data.pckl', 'rb') as users_data:  
            users = pickle.load(users_data) 
        users[user]["f_commission"] += commission
        with open('/var/www/webApp/users_data.pckl', 'wb') as users_data:
            pickle.dump(users, users_data)

    def make_order(side, price, unit):
        nonlocal open_buys, open_sells   ## if there is a order with same price do not make order
        if side == OrderSide.BUY and price in open_buys:
            return None
        if side == OrderSide.SELL and price in open_sells:
            return None
        
        result = None
        try:
            result = client.post_order(symbol = symbol, side=side, ordertype=OrderType.LIMIT, 
            quantity = Decimal("%.2f" % unit), price = Decimal("%.2f" % price), timeInForce=TimeInForce.GTC)
            open_buys.append(price) if side == OrderSide.BUY else open_sells.append(price)
        except Exception as e:
            print(e)
            return None
                       
        print(f"ORDER OPENED {result.side} -> {result.price}")
        return result

    def bulk_buy():
        nonlocal sell_order_count
        buy = client.post_order(symbol = symbol, side=OrderSide.BUY, ordertype=OrderType.MARKET, quantity=unit*5)
        price = client.get_mark_price(symbol = symbol).markPrice

        print(f"\nBULK BUY")
        print(buy)
        
        bulk_buy_orders = {}
        for i in range(1,6):
            sell = make_order(OrderSide.SELL, Decimal("%.2f" % (price + step*i)), unit)
            bulk_buy_orders[sell.orderId] = price
        sell_order_count = 5

        users = {}  ## Eldeki COIN miktarını doğru hesaplamak için bulk buyları kayıt et
        with open('/var/www/webApp/users_data.pckl', 'rb') as users_data:  
            users = pickle.load(users_data) 
        users[user]["f_bulk_buy_orders"] = bulk_buy_orders
        with open('/var/www/webApp/users_data.pckl', 'wb') as users_data:
            pickle.dump(users, users_data)
       
        return price

    def findmin_openOrders():
        orders = client.get_open_orders(symbol=symbol)
        price = 9999999
        orderId = None
        count = 0
        for order in orders:
            if order.side == "BUY":
                count += 1
                if float(order.price) < price:
                    price = float(order.price)
                    orderId = order.orderId
        return (orderId, count)

    def delete_buy_orders():
        orders = client.get_open_orders(symbol=symbol)
        for order in orders:
            if order.side == "BUY":
                try:
                    client.cancel_order(symbol=symbol, orderId=order.orderId)
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
            buy = make_order(OrderSide.BUY, Decimal("%.2f" % (price - step*i)), unit)
    
    # keep ex sell orders in user data
    ex_sell_orders = []
    orders = client.get_open_orders(symbol=symbol)
    for order in orders:
        if order.side == "SELL":
            ex_sell_orders.append(order.orderId)
    
    users = {}
    with open('/var/www/webApp/users_data.pckl', 'rb') as users_data:  
        users = pickle.load(users_data) 
    users[user]["f_ex_sell_orders"] = ex_sell_orders
    with open('/var/www/webApp/users_data.pckl', 'wb') as users_data:
        pickle.dump(users, users_data)

    #################################################################################################  

    initialize()
    while True:
        oldest_stream_data_from_stream_buffer = binance_com_websocket_api_manager.pop_stream_data_from_stream_buffer()
        
        if oldest_stream_data_from_stream_buffer:
            stream = json.loads(oldest_stream_data_from_stream_buffer)
        
            if stream["e"] == "ORDER_TRADE_UPDATE" and stream["o"]["o"] == "LIMIT" and stream["o"]["s"] == symbol and stream["o"]["X"] == "FILLED":
                price = float(stream["o"]["p"])
                
                try:
                    if stream["o"]["S"] == "SELL" and stream["o"]["i"] not in ex_sell_orders:
                        print(f"\nSELL -> {price}")
                        sell_order_count -= 1
                        try:
                            open_sells.remove(Decimal("%.2f" % price))
                        except: 
                            pass
                        buy = make_order(OrderSide.BUY, Decimal("%.2f" % (price - step)), unit)

                        if findmin_openOrders()[1] > grids:  #eğer gridden fazla buy order var ise en küçüğü iptal et
                            try:
                                canceled = client.cancel_order(symbol=symbol, orderId=findmin_openOrders()[0] )
                                print(f"CANCELED -> {canceled.price} ")
                                open_buys.remove( Decimal("%.2f" % float(canceled.price)) )
                            except:
                                pass
                                    
                        if sell_order_count == 0:
                            initialize()
                        increment()   ## increment sell_count to calculate reports
                        commission(float(stream["o"]["n"]))   

                    if stream["o"]["S"] == "BUY":
                        print(f"\nBUY -> {price} ")
                        try:
                            open_buys.remove(Decimal("%.2f" % price))
                        except: 
                            pass
                        sell = make_order(OrderSide.SELL, Decimal("%.2f" % (price + step)), unit )
                        sell_order_count += 1
                        buy = make_order(OrderSide.BUY, Decimal("%.2f" % (price - step*grids)) , unit )
                        commission(float(stream["o"]["n"]))   

                except Exception as e:
                    print(e)
                    time.sleep(60)
                    client = RequestClient(api_key=api, secret_key=secret, url='https://fapi.binance.com') if not bool_test else RequestClient(api_key=api, secret_key=secret, url="https://testnet.binancefuture.com")
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
    e =     int(sys.argv[5])
    api =   sys.argv[6]
    secret= sys.argv[7]
    bool_test = sys.argv[8] == "True"
    user =  sys.argv[9]
    
    bot(a, b, c, d, e, api, secret, bool_test, user)

