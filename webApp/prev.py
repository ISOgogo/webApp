from flask import Flask, render_template, request, flash, redirect, session
import os, signal, time, pickle
from multiprocessing import Process
import yuzdelik, r10_futures, last_trades, reports_week, reports_day

app = Flask(__name__)   
app.secret_key = "super secret key"

with open('/var/www/webApp/users_data.pckl','rb') as users_data:
    users = pickle.load(users_data)

bot = None

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/kullanici", methods=["POST", "GET"])
def kullanici():
    global users
    curr_user = request.args.get("user")

    if not curr_user:
        curr_user   = request.form.get("user")
        api         = request.form.get("api")
        secret      = request.form.get("secret")

        if curr_user and api and secret:
            with open('/var/www/webApp/users_data.pckl', 'wb') as users_data:
                users[curr_user] = {"api":api, "secret":secret}
                pickle.dump(users, users_data)

        elif not users.get(curr_user):   
            flash("Kullanıcı Bulunamadı")
            return redirect("/")
        
    pid =  users[curr_user].get("pid")
    if pid:
        try:
            os.kill(pid, 0)
            bot_control = True
        except:
            cot_control = False
    else:
        bot_control = False

    return render_template("kullanici.html", user = curr_user, bot_control = bot_control )

@app.route("/bot", methods=["POST","GET"])
def bot():
    global bot

    user   =    request.args.get("user")
    if not user:
        user = curr_user

    if request.form.get("return"):
        return redirect(f"/kullanici?user={user}")
    if request.form.get("stop"):
        while bot.is_alive():
            os.system(f"kill -9 {users[user]['pid']}")

    print(users)    
    api    =    users[user]["api"]
    secret =    users[user]["secret"]

    symbol =    request.form.get("coin")
    step   =    request.form.get("step")
    yuzde  =    request.form.get("yuzde")
    unit   =    request.form.get("unit")
    grids  =    request.form.get("grids")
    

    if len(request.form) >= 4:   #formdan gelen veriler symbol, step, yuzde vb leri içerirse 4ten büyük olur
        function =  yuzdelik.bot if yuzde else r10_futures.bot
        bot = Process(target= function, args=(symbol,step,unit,grids,api,secret))
        bot.start()

        with open('/var/www/webApp/users_data.pckl','wb') as users_data:
                users[user] = {"api":api,"secret":secret,"symbol":symbol,"step":float(step),
                    "unit":float(unit),"grids":int(grids),"pid":bot.pid}
                pickle.dump(users, users_data)
        
    
    c_bot = users[user]
    return render_template("bot.html", 
    trades = last_trades.trades(c_bot["symbol"], c_bot["api"], c_bot["secret"]), 
    report = reports_day.reports(c_bot["symbol"], c_bot["api"], c_bot["secret"]), 
    user = user, is_alive = bot.is_alive())

@app.route("/raporlar/<user>", methods=["POST","GET"])
def raporlar(user):
    c_bot = users[user]
    try:
        sym = c_bot["symbol"]
    except:
        flash("Daha Önce Bot Akif Etmediniz !")
        return redirect(f"/kullanici?user={user}")

    day  = reports_day.reports(c_bot["symbol"], c_bot["api"], c_bot["secret"])
    week = reports_week.reports(c_bot["symbol"], c_bot["api"], c_bot["secret"])
    trades = last_trades.trades(c_bot["symbol"], c_bot["api"], c_bot["secret"]) 

    return render_template("rapor.html", user = user, day = day, week = week, trades = trades)
