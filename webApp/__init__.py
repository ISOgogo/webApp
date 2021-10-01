from flask import Flask, render_template, request, flash, redirect, session
import os
import signal
import time
import pickle
from multiprocessing import Process
import yuzdelik
import r10_futures
import last_trades
import reports_week
import reports_day

app = Flask(__name__)
app.secret_key = "super secret key"
app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 0

users = {}
bots = {}

with open('/var/www/webApp/users_data.pckl', 'rb') as users_data:  # /var/www/webApp/
    users = pickle.load(users_data)


@app.after_request
def add_header(response):
    response.cache_control.max_age = 0
    return response

@app.route("/")
def index():
    return render_template("index.html")


@app.route("/kullanici", methods=["POST", "GET"])
def kullanici():
    global users, bots
    curr_user = request.args.get("user", default=None)
    login = ""
    if not curr_user:
        curr_user = request.form.get("register")
        login = request.form.get("login")
        api = request.form.get("api")
        secret = request.form.get("secret")

        if curr_user and api and secret:
            users[curr_user] = {"api": api, "secret": secret}
            with open('/var/www/webApp/users_data.pckl', 'wb') as users_data:
                pickle.dump(users, users_data)

        elif not users.get(login):
            flash("Kullanıcı Bulunamadı")
            return redirect("/")

    if not curr_user:
        curr_user = login

    is_alive = True if bots.get(curr_user) and bots.get(
        curr_user).is_alive() else False
    return render_template("kullanici.html", user=curr_user, bot_control=is_alive)


@app.route("/bot", methods=["POST", "GET"])
def bot():
    global users, bots

    user = request.args.get("user")

    if request.form.get("return"):
        return redirect(f"/kullanici?user={user}")
    if request.form.get("stop"):
        while bots[user].is_alive():
            try:
                os.system(f"kill -9 {bots[user].pid}")
            except:
                pass

    with open('/var/www/webApp/users_data.pckl', 'rb') as users_data:
        users = pickle.load(users_data)

    api = users[user]["api"]
    secret = users[user]["secret"]

    symbol = request.form.get("coin")
    step = request.form.get("step")
    yuzde = request.form.get("yuzde")
    unit = request.form.get("unit")
    grids = request.form.get("grids")

    if len(request.form) >= 4:  # formdan gelen veriler symbol, step, yuzde vb leri içerirse 4ten büyük olur
        function = yuzdelik.bot if yuzde else r10_futures.bot
        bot = Process(target=function, args=(
            symbol, step, unit, grids, api, secret))
        time.sleep(0.3)
        bot.start()
        time.sleep(1)
        bots[user] = bot

        with open('/var/www/webApp/users_data.pckl', 'wb') as users_data:
            users[user] = {"api": api, "secret": secret, "symbol": symbol, "step": float(step),
                           "unit": float(unit), "grids": int(grids)}
            pickle.dump(users, users_data)

    c_bot = users[user]
    is_alive = True if bots.get(user) and bots.get(user).is_alive() else False

    return render_template("bot.html",
                           trades=last_trades.trades(
                               c_bot["symbol"], c_bot["api"], c_bot["secret"]),
                           report=reports_day.reports(
                               c_bot["symbol"], c_bot["api"], c_bot["secret"]),
                           user=user, is_alive=is_alive)


@app.route("/raporlar/<user>", methods=["POST", "GET"])
def raporlar(user):
    c_bot = users[user]
    try:
        sym = c_bot["symbol"]
    except:
        flash("Daha Önce Bot Akif Etmediniz !")
        return redirect(f"/kullanici?user={user}")

    day = reports_day.reports(c_bot["symbol"], c_bot["api"], c_bot["secret"])
    week = reports_week.reports(c_bot["symbol"], c_bot["api"], c_bot["secret"])
    trades = last_trades.trades(c_bot["symbol"], c_bot["api"], c_bot["secret"])

    return render_template("rapor.html", user=user, day=day, week=week, trades=trades)
