from flask import Flask, request
import telegram
import os

TOKEN = "YOUR_TELEGRAM_BOT_TOKEN"
bot = telegram.Bot(token=TOKEN)

app = Flask(__name__)

@app.route(f"/webhook/{TOKEN}", methods=["POST"])
def webhook_handler():
    update = telegram.Update.de_json(request.get_json(force=True), bot)

    # ====> main.py handler'larini shu yerga ulaysiz
    # Masalan, /start bo‘lsa:
    if update.message and update.message.text == "/start":
        bot.sendMessage(chat_id=update.message.chat_id, text="Bot ishga tushdi!")

    return "OK", 200


@app.route("/", methods=["GET"])
def home():
    return "Webhook server ishlayapti!", 200


if __name__ == "__main__":
    app.run()
