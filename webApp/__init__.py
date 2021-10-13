from flask import Flask, render_template, request, flash, redirect, session
import os, signal, time, pickle
from multiprocessing import Process
import yuzdelik, r10_futures, last_trades, reports_week, reports_day

app = Flask(__name__)
app.secret_key = "super secret key"
app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 0

users = {}

def read_users():
    global users
    with open('/var/www/webApp/users_data.pckl', 'rb') as users_data:  
        users = pickle.load(users_data)

def write_users():
    global users
    with open('/var/www/webApp/users_data.pckl', 'wb') as users_data:
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
    return render_template("kullanici.html", user=curr_user, bot_control=bot_control)
    


@app.route("/bot", methods=["POST", "GET"])
def bot():
    global users
    read_users()
    user = request.args.get("user")

    if request.form.get("return"):
        return redirect(f"/kullanici?user={user}")
    if request.form.get("stop"):
        for i in range(100):
            try:
                os.system(f"kill -9 {users[user]['pid']}")
            except Exception as e:
                print(e.message)
                pass
    
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
        bot = Process(target=function, args=(symbol, step, unit, grids, api, secret))
        time.sleep(0.3)
        bot.start()
        time.sleep(0.3)

        users[user] = {"api": api, "secret": secret, "symbol": symbol, "step": float(step),
                       "unit": float(unit), "grids": int(grids), "pid":bot.pid}
        write_users()

    c_bot = users[user]
    profit_per_sell = c_bot["unit"] * c_bot["step"] 
    day = reports_day.reports(c_bot["symbol"], c_bot["api"], c_bot["secret"])

    return render_template("bot.html",
    trades=(profit_per_sell*day[1],day[0],day[1]),
    report=reports_day.reports(c_bot["symbol"], c_bot["api"], c_bot["secret"]),
    user=user)


@app.route("/raporlar/<user>", methods=["POST", "GET"])
def raporlar(user):
    global users
    read_users()

    c_bot = users[user]
    is_alive = request.args.get("bot")
    try:
        sym = c_bot["symbol"]
    except:
        flash("Daha Önce Bot Akif Etmediniz !")
        return redirect(f"/kullanici?user={user}&bot=False")

    profit_per_sell = c_bot["unit"] * c_bot["step"] 
    day = reports_day.reports(c_bot["symbol"], c_bot["api"], c_bot["secret"])
    week = reports_week.reports(c_bot["symbol"], c_bot["api"], c_bot["secret"])
    trades = last_trades.trades(c_bot["symbol"], c_bot["api"], c_bot["secret"])
    
    return render_template("rapor.html", user= user, day= (profit_per_sell*day[1],day[0],day[1]), 
                    week=(profit_per_sell*week[1],week[0],week[1]), trades=trades, bot_control = is_alive)

