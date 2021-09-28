from flask import Flask, render_template, request, flash, redirect, session
import os, signal, time
from multiprocessing import Process
import yuzdelik, r10_futures, last_trades, reports

app = Flask(__name__)
app.secret_key = "super secret key"

users = {}
curr_user = ""
bot = None

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/kullanici", methods=["POST", "GET"])
def kullanici():
    global users, curr_user
    curr_user = request.args.get("user")

    if not curr_user:
        curr_user   = request.form.get("user")
        api         = request.form.get("api")
        secret      = request.form.get("secret")

        if curr_user and api and secret:
            users[curr_user] = {"api":api, "secret":secret}
            
        elif not users.get(curr_user):   
            flash("Kullanıcı Bulunamadı")
            return redirect("/")

    session["curr_user"] = users[curr_user]
    
    try:
        bot_control = bot.is_alive()
    except:
        bot_control = False

    return render_template("kullanici.html", user = curr_user, bot_control = bot_control )

@app.route("/bot", methods=["POST","GET"])
def bot():
    global bot
    if request.form.get("return"):
        return redirect(f"/kullanici?user={curr_user}")
    if request.form.get("stop"):
        while bot.is_alive():
            os.system(f"kill -9 {bot.pid}")

    user   =    request.args.get("user")
    if not user:
        user = curr_user
    
    api    =    session.get('curr_user')["api"]
    secret =    session.get('curr_user')["secret"]

    symbol =    request.form.get("coin")
    step   =    request.form.get("step")
    yuzde  =    request.form.get("yuzde")
    unit   =    request.form.get("unit")
    grids  =    request.form.get("grids")
    

    if len(request.form) >= 4:   #formdan gelen veriler symbol, step, yuzde vb leri içerirse 4ten büyük olur
        function =  yuzdelik.bot if yuzde else r10_futures.bot
        bot = Process(target= function, args=(symbol,step,unit,grids,api,secret))
        bot.start()
        users[user] = {"api":api,"secret":secret,"symbol":symbol,"step":float(step),
                    "unit":float(unit),"grids":int(grids),"pid":bot.pid}
        
    
    c_bot = users[user]
    return render_template("bot.html", 
    trades = last_trades.trades(c_bot["symbol"], c_bot["api"], c_bot["secret"]), 
    report = reports.reports(c_bot["symbol"], c_bot["api"], c_bot["secret"], c_bot["step"]), 
    profit_per_sell = c_bot["step"]*c_bot["unit"], user = curr_user, is_alive = bot.is_alive())
