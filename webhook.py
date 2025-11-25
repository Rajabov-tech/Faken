import os
from aiohttp import web
from aiogram import Bot, Dispatcher
from aiogram.webhook.aiohttp_server import SimpleRequestHandler, setup_application

from main import dp, bot, TELEGRAM_BOT_TOKEN  # main.py ichidagi dp ishlatiladi

WEBHOOK_URL = f"https://{os.getenv('PA_USERNAME')}.pythonanywhere.com/webhook/{TELEGRAM_BOT_TOKEN}"
WEBHOOK_PATH = f"/webhook/{TELEGRAM_BOT_TOKEN}"

async def on_startup(app):
    await bot.set_webhook(WEBHOOK_URL)

async def on_shutdown(app):
    await bot.delete_webhook()

def main():
    app = web.Application()

    SimpleRequestHandler(dispatcher=dp, bot=bot).register(app, path=WEBHOOK_PATH)
    setup_application(app, dp, bot=bot)

    app.on_startup.append(on_startup)
    app.on_shutdown.append(on_shutdown)

    web.run_app(app, host="0.0.0.0", port=8000)

if __name__ == "__main__":
    main()
