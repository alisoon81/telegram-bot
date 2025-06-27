from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, ContextTypes, CallbackQueryHandler, MessageHandler, filters
from telegram.constants import ParseMode
from flask import Flask, request, Response
import os
import json
import hashlib
import asyncio

BOT_TOKEN = os.getenv("BOT_TOKEN")
APP_URL = os.getenv("APP_URL")  # مثلا https://telegram-bot-xq3r.onrender.com

TRANSLATION_FILE = "translations.json"

def load_translations():
    if os.path.exists(TRANSLATION_FILE):
        with open(TRANSLATION_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

def save_translations(data):
    with open(TRANSLATION_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False)

translation_store = load_translations()

def shorten_file_id(file_id: str) -> str:
    return hashlib.md5(file_id.encode()).hexdigest()

async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message.caption or "|" not in update.message.caption:
        await update.message.reply_text(
            "❌ لطفاً کپشن عکس رو به این صورت بنویس:\n`متن انگلیسی | ترجمه فارسی`",
            parse_mode=ParseMode.MARKDOWN)
        return

    original, translated = map(str.strip, update.message.caption.split("|", 1))
    photo = update.message.photo[-1]
    file_id = photo.file_id

    short_id = shorten_file_id(file_id)
    translation_store[short_id] = translated
    save_translations(translation_store)

    await context.bot.send_photo(
        chat_id="@your_channel_username_or_id",  # کانال خودت رو اینجا بگذار
        photo=file_id,
        caption=original,
        reply_markup=InlineKeyboardMarkup([[
            InlineKeyboardButton("Translate", callback_data=f"translate_{short_id}")
        ]])
    )

    await update.message.reply_text("✅ پست در کانال منتشر شد.")

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    data = query.data
    try:
        if data.startswith("translate_"):
            short_id = data.split("_", 1)[1]
            translation = translation_store.get(short_id, "❌ ترجمه‌ای یافت نشد.")
            await query.answer(text=translation, show_alert=True)
        else:
            await query.answer()
    except Exception as e:
        print(f"⚠️ خطا در پاسخ به دکمه: {e}")
        try:
            await query.answer(text="⏱ دکمه منقضی شده یا خطایی پیش اومده.", show_alert=True)
        except:
            pass

application = ApplicationBuilder().token(BOT_TOKEN).build()
application.add_handler(MessageHandler(filters.PHOTO, handle_photo))
application.add_handler(CallbackQueryHandler(button_handler))

flask_app = Flask(__name__)

@flask_app.route('/')
def home():
    return "ربات فعال است 🚀"

@flask_app.route(f'/{BOT_TOKEN}', methods=['POST'])
def webhook():
    update = Update.de_json(request.get_json(force=True), application.bot)
    asyncio.run(application.process_update(update))
    return Response("ok", status=200)

if __name__ == '__main__':
    async def main():
        await application.bot.set_webhook(f"{https://telegram-bot-xq3r.onrender.com}/{BOT_TOKEN}")
        print(f"✅ وب‌هوک ست شد روی: {https://telegram-bot-xq3r.onrender.com}/{BOT_TOKEN}")
        flask_app.run(host="0.0.0.0", port=8080)

    asyncio.run(main())
