from flask import Flask
from threading import Thread

app = Flask(__name__)

@app.route('/')
def home():
    return "I'm alive!"

def run():
    app.run(host='0.0.0.0', port=8080, debug=False)

def keep_alive():
    server_thread = Thread(target=run, daemon=True)
    server_thread.start()