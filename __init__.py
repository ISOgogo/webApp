from flask import Flask, render_template, request, flash, redirect, session
import os, signal, time
from multiprocessing import Process
import r10_futures

app = Flask(__name__)
app.secret_key = "super secret key"

users = {}
curr_user = ""
bot = None

@app.route("/")
def hello_world():
    global curr_user
    curr_user = ""
    return render_template("index.html")

@app.route("/kullanici", methods=["POST", "GET"])
def kullanici():
    global users, curr_user
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
    return render_template("kullanici.html", user = curr_user)

@app.route("/bot", methods=["POST","GET"])
def bot():
    global bot
    api    =    session.get('curr_user')["api"]
    secret =    session.get('curr_user')["secret"]

    symbol =    request.form.get("coin")
    step   =    request.form.get("step")
    unit   =    request.form.get("unit")
    grids  =    request.form.get("grids")

    bot = Process(target=r10_futures.bot, args=(symbol,step,unit,grids,api,secret))
    bot.start()
    return render_template("bot.html")

    
@app.route("/stop", methods = ["GET", "POST"])
def stop():
    global bot
    bot.terminate()
    
    return redirect("/kullanici")