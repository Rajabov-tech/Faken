# wrapper.py
from threading import Thread
from flask import Flask
import subprocess

# Flask server
app = Flask("")

@app.route("/")
def home():
    return "Bot is running"

def run_flask():
    app.run(host="0.0.0.0", port=5000)

if __name__ == "__main__":
    # Flask serverni alohida threadda ishga tushirish
    Thread(target=run_flask).start()

    # Asosiy botni ishga tushirish (main.py bilan bir papkada)
    subprocess.run(["python", "main.py"])
