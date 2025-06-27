from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, MessageHandler, filters, CallbackQueryHandler, ContextTypes
from telegram.constants import ParseMode
from flask import Flask
from threading import Thread
import nest_asyncio
import asyncio
import os
import json
import hashlib

nest_asyncio.apply()

BOT_TOKEN = os.getenv("BOT_TOKEN")
CHANNEL_ID = int(os.getenv("CHANNEL_ID"))

TRANSLATION_FILE = "translations.json"

def load_translations():
    if os.path.exists(TRANSLATION_FILE):
        with open(TRANSLATION_FILE, "r") as f:
            return json.load(f)
    return {}

def save_translations(data):
    with open(TRANSLATION_FILE, "w") as f:
        json.dump(data, f)

translation_store = load_translations()

def shorten_file_id(file_id: str) -> str:
    # هش MD5 از file_id می‌سازیم که 32 کاراکتر هست
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

    sent_msg = await context.bot.send_photo(
        chat_id=CHANNEL_ID,
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

async def start_bot():
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(MessageHandler(filters.PHOTO, handle_photo))
    app.add_handler(CallbackQueryHandler(button_handler))
    print("✅ ربات آماده اجراست...")
    await app.run_polling()

flask_app = Flask('')

@flask_app.route('/')
def home():
    return "ربات فعاله 🚀"

def run():
    flask_app.run(host="0.0.0.0", port=8080)

if __name__ == "__main__":
    Thread(target=run).start()
    asyncio.run(start_bot())
