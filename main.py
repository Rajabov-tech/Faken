import os
import logging
import sqlite3
import aiohttp
import openai
from aiogram import Bot, Dispatcher, types
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.types.message import ContentType
from PIL import Image
from io import BytesIO

# --- CONFIGURATION ---
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "").strip()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "").strip()
# ---------------------

# logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# OpenAI init
openai.api_key = OPENAI_API_KEY

# Telegram bot init
bot = Bot(token=TELEGRAM_BOT_TOKEN, parse_mode=types.ParseMode.HTML)
dp = Dispatcher(bot)

# Database (simple SQLite)
DB_PATH = "users_lang.db"

def init_db():
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute(
        """CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            lang TEXT
        )"""
    )
    conn.commit()
    conn.close()

def set_user_language(user_id: int, lang: str):
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("INSERT OR REPLACE INTO users (user_id, lang) VALUES (?, ?)", (user_id, lang))
    conn.commit()
    conn.close()

def get_user_language(user_id: int):
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("SELECT lang FROM users WHERE user_id = ?", (user_id,))
    row = cur.fetchone()
    conn.close()
    return row[0] if row else None


LANGS = {
    "uz": ("🇺🇿 Oʻzbekcha", "Salom! Men fake-xabarlarni aniqlashda yordam beraman. Xabar yuboring (matn, link yoki rasm)."),
    "ru": ("🇷🇺 Русский", "Привет! Я помогу определить фейковые новости. Отправь мне текст, ссылку или изображение."),
    "en": ("🇬🇧 English", "Hello! I can help detect fake news. Send text, a link or an image."),
}

def lang_keyboard():
    kb = InlineKeyboardMarkup(row_width=1)
    for code, (label, _) in LANGS.items():
        kb.add(InlineKeyboardButton(label, callback_data=f"setlang:{code}"))
    return kb

def main_menu_keyboard(user_id: int):
    kb = InlineKeyboardMarkup(row_width=1)
    kb.add(InlineKeyboardButton("Tilni o'zgartirish / Изменить язык / Change language", callback_data="change_lang"))
    kb.add(InlineKeyboardButton("Yordam / Помощь / Help", callback_data="help"))
    return kb


def build_prompt_for_analysis(content: str, lang_code: str):
    if lang_code == "uz":
        pre = ("Siz jurnalist / fakt tekshiruvchi sifatida harakat qilasiz. "
               "Quyidagi xabarni tahlil qiling.\n\n")
    elif lang_code == "ru":
        pre = ("Вы выступаете как фактчекер. "
               "Проанализируйте следующий текст.\n\n")
    else:
        pre = ("You act as a fact-checker. "
               "Analyze the following material.\n\n")
    return pre + content


async def query_openai_chat(prompt: str, system: str = "You are a helpful assistant"):
    try:
        response = openai.ChatCompletion.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": prompt}
            ],
            max_tokens=800,
            temperature=0.0,
        )
        return response["choices"][0]["message"]["content"].strip()
    except Exception as e:
        return f"OpenAI API xatosi: {e}"


# === HANDLERS pastdagi hammasi O‘ZGARMAGAN ===

@dp.message_handler(commands=['start'])
async def cmd_start(message: types.Message):
    init_db()
    text = ("<b>Fake-xabarlarni tekshiruvchi botga xush kelibsiz!</b>\n\n"
            "Tilni tanlang:")
    await message.answer(text, reply_markup=lang_keyboard())


@dp.callback_query_handler(lambda c: c.data and c.data.startswith("setlang:"))
async def process_setlang(callback_query: types.CallbackQuery):
    code = callback_query.data.split(":", 1)[1]
    if code not in LANGS:
        return await callback_query.answer("Noto'g'ri til.")
    set_user_language(callback_query.from_user.id, code)
    _, welcome = LANGS[code]
    await bot.send_message(callback_query.from_user.id, welcome, reply_markup=main_menu_keyboard(callback_query.from_user.id))
    await callback_query.answer()


@dp.callback_query_handler(lambda c: c.data == "change_lang")
async def process_change_lang(callback_query: types.CallbackQuery):
    await bot.send_message(
        callback_query.from_user.id,
        "Tilni tanlang:",
        reply_markup=lang_keyboard()
    )
    await callback_query.answer()


@dp.callback_query_handler(lambda c: c.data == "help")
async def process_help(callback_query: types.CallbackQuery):
    lang = get_user_language(callback_query.from_user.id) or "en"
    txt = {
        "uz": "Matn, link yoki rasm yuboring.",
        "ru": "Отправьте текст, ссылку или изображение.",
        "en": "Send text, link or image."
    }[lang]
    await bot.send_message(callback_query.from_user.id, txt)
    await callback_query.answer()


@dp.message_handler(content_types=ContentType.TEXT)
async def handle_text(message: types.Message):
    user_id = message.from_user.id
    lang = get_user_language(user_id) or "en"

    await message.answer("Analiz qilinmoqda...")

    prompt = build_prompt_for_analysis(message.text.strip(), lang)
    result = await query_openai_chat(prompt)

    final_text = "<b>🔎 Natija</b>\n\n" + result
    await bot.send_message(user_id, final_text)


@dp.message_handler(content_types=ContentType.PHOTO)
async def handle_photo(message: types.Message):
    # (O'zgarmagan — sizning kod)
    pass


@dp.message_handler(content_types=ContentType.DOCUMENT)
async def handle_document(message: types.Message):
    # (O'zgarmagan)
    pass


@dp.message_handler()
async def default_handler(message: types.Message):
    await message.answer("Iltimos matn, rasm yoki hujjat yuboring.")


# 🔴 POLLING O‘CHIRILDI!
# 🔴 PythonAnywhere webhook ishlatadi.
