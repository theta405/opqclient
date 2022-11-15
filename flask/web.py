from flask import Flask, request, render_template, url_for
from subprocess import Popen, PIPE
from time import sleep
from sys import path
from pathlib import Path
ROOT = Path(__file__).parent
path.append(str(ROOT.parents[0]))
import public

TEMPLATES = ROOT/"templates"
START_SH = ROOT/"start.sh"
STOP_SH = ROOT/"stop.sh"
MAX_TRIALS = 30

app = Flask(__name__,  template_folder = str(TEMPLATES))

@app.route("/control", methods = ("GET", "POST"))
def info():
    if request.method == "POST":
        count = 0
        control = request.get_json()["control"] == "SHUTDOWN"
        Popen(f"{STOP_SH if control else START_SH}")
        while checkServer()  == control:
            sleep(1)
            count += 1
            if count >= MAX_TRIALS: return "FAILED"
        return "SUCCESS"
    return render_template("info.html", running = checkServer())

@app.route("/style")
def style():
    return render_template("style.html"), 404

@app.route("/post", methods=["POST", "GET"])
def login():
    if request.method == "POST":
        public.sendMsg(1907867998, None, f"Hello World\nPath: {__file__}\nQQ: {public.QQ}")
        return request.form["username"]

def checkServer():
    server = Popen("ps -aux | grep server.jar | grep -v grep", shell = True, stdout = PIPE)
    result, _ = server.communicate()
    server.wait()
    return result.decode() != ""