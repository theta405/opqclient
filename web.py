from flask import Flask

app = Flask(__name__)

@app.route("/")
def hello():
    return f"<p>Hello World<br />Path: {__file__}</p>"