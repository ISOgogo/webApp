from flask import Flask, render_template, request, flash, redirect, session
import os, signal, time, pickle
from datetime import datetime
from multiprocessing import Process
import yuzdelik, r10_futures, last_trades, reports_day, cancel_buy_orders, open_orders, test_routes
from test_routes import testnet

app = Flask(__name__)
app.register_blueprint(testnet)
app.secret_key = "super secret key"
app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 0

users = {}

def read_users():
    global users
    with open('users_data.pckl', 'rb') as users_data:  
        users = pickle.load(users_data)

def write_users():
    global users
    with open('users_data.pckl', 'wb') as users_data:
        pickle.dump(users, users_data)


def is_alive(user):
    try:
        users[user]["pid"]
    except:
        return False
    return True

@app.after_request
def add_header(response):
    response.cache_control.max_age = 0
    return response

@app.route("/")
def index():
    global users

    return render_template("index.html")


@app.route("/kullanici", methods=["POST", "GET"])
def kullanici():
    global users
    read_users()

    curr_user = request.args.get("user", default=None)
    login = ""

    if not curr_user:
        curr_user = request.form.get("register")
        login = request.form.get("login")
        api = request.form.get("api")
        secret = request.form.get("secret")

        if curr_user and api and secret:
            users[curr_user] = {"api": api, "secret": secret}
            write_users()

        elif not users.get(login):
            flash("Kullanıcı Bulunamadı")
            return redirect("/")

    if not curr_user:
        curr_user = login

    print(users[curr_user])
    bot_control = request.args.get("bot", default = is_alive(curr_user), type = lambda x: x == "True")     
    
    c_bot = users[curr_user]
    
    day = None
    trades = None
    commission = 0 if not c_bot.get("commission") else "%.2f" % c_bot.get("commission")

    if bot_control: 
        day = reports_day.reports(c_bot["symbol"], c_bot["api"], c_bot["secret"], False, c_bot["unit"], c_bot["step"], c_bot["time"])
        trades = last_trades.trades(c_bot["symbol"], c_bot["api"], c_bot["secret"], False)
    
    try:
        sym = c_bot["ex_sell_orders"]
        buy_stats = open_orders.open_orders(c_bot["symbol"], c_bot["api"], c_bot["secret"], False, c_bot["step"], c_bot["ex_sell_orders"], c_bot['bulk_buy_orders'])
        profit_per_sell = c_bot["unit"] * c_bot["step"] 
        all_time = ( c_bot["sell_count"], "%.2f" % (profit_per_sell*c_bot["sell_count"]) )
    except:
        buy_stats = (0,0)
        all_time = (0,0)
        
    return render_template("kullanici.html", user=curr_user, bot_control=bot_control, 
    day=day, all_time=all_time, trades=trades, buy_stats = buy_stats, commission = commission)
    
@app.route("/bot", methods=["POST", "GET"])
def bot():
    global users
    read_users()
    user = request.args.get("user")
    
    if request.form.get("stop"):
        for i in range(100):
            time.sleep(0.01)
            try:
                os.system(f"kill -9 {users[user]['pid']}")
            except Exception as e:
                print(e)
                pass
        
        cancel_buy_orders.cancel(users[user]['api'], users[user]['secret'], False, users[user]['symbol'])
        users[user].pop("pid", None)
        write_users()
        return redirect(f"/kullanici?user={user}&bot=False")

    api = users[user]["api"]
    secret = users[user]["secret"]

    symbol = request.form.get("coin")
    step = request.form.get("step")
    yuzde = request.form.get("yuzde")
    unit = request.form.get("unit")
    grids = request.form.get("grids")

    if len(request.form) >= 4:  # formdan gelen veriler symbol, step, yuzde vb leri içerirse 4ten büyük olur
        function = yuzdelik.bot if yuzde else r10_futures.bot
        bot = Process(target=function, args=(symbol, step, unit, grids, api, secret, False, user))
        time.sleep(0.3)
        bot.start()
        now = datetime.now()
        time.sleep(0.3)

        users[user] = {"api": api, "secret": secret, "symbol": symbol, "step": float(step), "unit": float(unit),
                    "grids": int(grids), "pid":bot.pid, "sell_count": 0, "time":now, "commission": 0.0}
        write_users()

    c_bot = users[user]

    return redirect(f"/kullanici?user={user}&bot=True")




# @app.route("/raporlar/<user>", methods=["POST", "GET"])
# def raporlar(user):
#     global users
#     read_users()
#     c_bot = users[user]

#     is_alive = request.args.get("bot")
#     try:
#         sym = c_bot["symbol"]
#     except:
#         flash("Daha Önce Bot Akif Etmediniz !")
#         return redirect(f"/kullanici?user={user}&bot=False")

#     profit_per_sell = c_bot["unit"] * c_bot["step"] 

#     day = reports_day.reports(c_bot["symbol"], c_bot["api"], c_bot["secret"], c_bot["unit"], c_bot["step"], c_bot["time"])
#     week = ( "%.2f" % (profit_per_sell*c_bot["sell_count"]), c_bot["sell_count"])
#     trades = last_trades.trades(c_bot["symbol"], c_bot["api"], c_bot["secret"])
    
#     return render_template("rapor.html", user= user, day=day,
#                     week=week, trades=trades, bot_control = is_alive)

