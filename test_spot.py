from binance import Client
from decimal import *
import time
import sys

api = "CHa8RCru7jJ8tze1lVYrjLK2Pxg5XZksszhl72U4QbR3sbTiKhJLOp4uPBuhuplJ"
secret = "ndk2J3V21kauoeeU151nTIohgWNb16Fsh2hGdZN5J3QSP1bJt2waFD7squFj8y28"
client = Client(api, secret, testnet=True)
unit = 0.05
step = 0.2
grids = 5
symbol = "BNBUSDT"
last_tradeId = Decimal(0)
kirik_list = []

############################################################################# Helper Functions
def make_order(side, price, unit):
    result = None
    c = 0
    while not result and c<20:
        c+=1
        try:
            result = client.create_order(symbol = symbol, side=side, 
    type=Client.ORDER_TYPE_LIMIT, quantity=unit, price = price, timeInForce=Client.TIME_IN_FORCE_GTC)
        except:
            pass
    print(f"ORDER OPENED {result['side']} -> {result['price']}")
    return result


def bulk_buy():
    
    buy = client.create_order(symbol = symbol, side=Client.SIDE_BUY, type=Client.ORDER_TYPE_MARKET, quantity=unit*5)
    buy_price = float(buy["fills"][0]["price"])
    
    print(f"BULK BUY")
    print(buy)
    for i in range(1,6):
        sell = make_order(Client.SIDE_SELL, Decimal("%.2f" % (buy_price + step*i)), unit)
    return buy_price

def initialize():
    global last_tradeId, kirik_list
    kirik_list = []
    price = bulk_buy()
    for i in range(1, grids+1):
        buy = make_order(Client.SIDE_BUY, Decimal("%.2f" % (price - step*i)), unit)
        
    last_tradeId = client.get_my_trades(symbol=symbol, limit=1)[0]["id"]

def find_in_openOrders(price):
    orders = client.get_open_orders(symbol=symbol)
    for order in orders:
        if float(order["price"]) == float(price):
            return True
    return False

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

        
#################################################################################################

delete_buy_orders()
initialize()

while True:    
    try:
        time.sleep(1)
    
        if float(client.get_asset_balance(asset=symbol[:-4])["locked"]) <= unit:
            delete_buy_orders()
            print("Initialize")
            initialize() 
        
        curr_trades = client.get_my_trades(symbol=symbol, fromId=last_tradeId)[1:]
        # Ani fiyat değişimlerinde çok order aynı anda fill oluyor bazen for döngüsü ile incelenebilir

        for curr_trade in curr_trades:
            
            order = client.get_order(symbol=symbol, orderId=curr_trade["orderId"])

            if order["orderId"] in kirik_list:
                continue
            elif float(curr_trade["qty"]) < unit:
                kirik_list.append(order["orderId"])
                
                
            price = float(order["price"])
            if price == 0:
                continue

            if order["side"] == "SELL":  #Eğer son trade satış ise bir aşağı kademeye alış ver
                print(f"SELL -> {order['price']} ")
                buy = make_order(Client.SIDE_BUY, Decimal("%.2f" % (price - step)), unit )               

                if findmin_openOrders()[1] > grids:  #eğer gridden fazla buy order var ise en küçüğü iptal et
                    deleted = None
                    for i in range(10):
                        try:
                            deleted = client.cancel_order(symbol=symbol, orderId=findmin_openOrders()[0] )
                        except:
                            pass
                        if deleted:
                            break
            
                                        
            if order["side"] == "BUY": #Eğer son trade alış ise en aşağı kademeye alış ver ve bir üste satış koy
                print(f"BUY -> {order['price']} ")
                sell = make_order(Client.SIDE_SELL, Decimal("%.2f" % (price + step)), unit )
                found = find_in_openOrders(price - step*grids)
                if not found: 
                    buy = make_order(Client.SIDE_BUY, Decimal("%.2f" % (price - step*grids)) , unit )
                
        if curr_trades:
            last_tradeId = curr_trades[-1]["id"]
    except Exception as e:
        print(e)
        time.sleep(10)
        client = Client(api, secret, testnet=True)
        continue
print("Bot Durdu")