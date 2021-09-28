from binance_f import RequestClient
from binance_f.constant.test import *
from binance_f.base.printobject import *
from binance_f.model.constant import *
from decimal import *
import time
import sys

def argument_converter(fn):
    def wrapper(symbol, step, unit, grids, api, secret):
        return fn(symbol, float(step), float(unit), int(grids), api ,secret)
    return wrapper

@argument_converter
def bot(symbol, step, unit, grids, api, secret):

    client = RequestClient(api_key=api, secret_key=secret, url="https://testnet.binancefuture.com")

    symbol = symbol + "USDT"
    last_tradeId = Decimal(0)
    kirik_list = []

    try:
        client.change_margin_type(symbol=symbol, marginType=FuturesMarginType.ISOLATED)
    except:
        pass
    client.change_initial_leverage(symbol=symbol, leverage = 1)

    ############################################################################# Helper Functions
    def make_order(side, price, unit):
        result = None

        while not result:
            try:
                result = client.post_order(symbol = symbol, side=side, 
        ordertype=OrderType.LIMIT, quantity=unit, price = price, timeInForce=TimeInForce.GTC)
            except:
                pass
        return result


    def bulk_buy():
        
        buy = client.post_order(symbol = symbol, side=OrderSide.BUY, 
            ordertype=OrderType.MARKET, quantity=unit*5)
        buy_price = client.get_mark_price(symbol = symbol).markPrice
        
        curr_price = buy_price
        for i in range(1,6):
            curr_price = curr_price*(100+step)/100
            sell = make_order(OrderSide.SELL, Decimal("%.2f" % curr_price), unit)
        return buy_price

    def initialize():
        nonlocal last_tradeId, kirik_list
        kirik_list = []

        curr_price = bulk_buy()
        for i in range(1, grids+1):
            curr_price = curr_price*100/(100+step)
            buy = make_order(OrderSide.BUY, Decimal("%.2f" % curr_price), unit)
        last_tradeId = client.get_account_trades(symbol=symbol, limit=1)[0].id

    def findmin_openOrders():
        orders = client.get_open_orders(symbol=symbol)
        price = Decimal(999999999)
        orderId = None
        count = 0
        for order in orders:
            if order.side == "BUY":
                count += 1
                if order.price < price:
                    price = order.price
                    orderId = order.orderId
        return (orderId, count)
    def delete_buy_orders():
        orders = client.get_open_orders(symbol=symbol)
        for order in orders:
            if order.side == "BUY":
                client.cancel_order(symbol=symbol, orderId=order.orderId)
    def sym_index():
        for index, sym in enumerate(client.get_position_v2() ):   #Açık pozisyonumuzda ne kadar bakiye olduğunu 
            if sym.symbol == symbol:                              #hızlıca görmek için indexini buluyoruz
                return index
    #################################################################################################

    delete_buy_orders()
    initialize()

    while True:
        symbol_index = sym_index()	
        if client.get_position_v2()[symbol_index].positionAmt <= 0:
            client.cancel_all_orders(symbol=symbol)
            initialize() 
            
        curr_trades = client.get_account_trades(symbol=symbol, fromId=last_tradeId)[1:]
        # Ani fiyat değişimlerinde çok order aynı anda fill oluyor bazen for döngüsü ile incelenebilir
        
        for curr_trade in curr_trades:

            order = client.get_order(symbol=symbol, orderId=curr_trade.orderId)

            if order.orderId in kirik_list:
                continue
            elif curr_trade.qty < unit:
                kirik_list.append(order.orderId)
                
                
            price = float(order.price)

            if curr_trade.side == "SELL":  #Eğer son trade satış ise bir aşağı kademeye alış ver
                
                buy = make_order(OrderSide.BUY, Decimal("%.2f" % (price*100/(100+step))), unit )               

                deleted = None
                for i in range(10):
                    try:
                        deleted = client.cancel_order(symbol=symbol, orderId=findmin_openOrders()[0] )
                    except:
                        pass
                    if deleted:
                        break
                

                                        
            if curr_trade.side == "BUY": #Eğer son trade alış ise en aşağı kademeye alış ver ve bir üste satış koy
                sell = make_order(OrderSide.SELL, Decimal("%.2f" % (price*(100+step)/100) ), unit )
                
                curr_price = price
                for i in range(grids):
                    curr_price = curr_price/(100+step)*100
                buy = make_order(OrderSide.BUY, Decimal("%.2f" %   curr_price ) , unit )
                
        if curr_trades:
            last_tradeId = curr_trades[-1].id

if __name__ == "__main__":
    a =     sys.argv[1]
    b =     float(sys.argv[2])
    c =     float(sys.argv[3])
    d =     int(sys.argv[4])
    api =   sys.argv[5]
    secret= sys.argv[6]

    bot(a, b, c, d, api, secret)
