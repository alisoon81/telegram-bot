import os
import json
import hashlib
import nest_asyncio
import asyncio
from flask import Flask, request, abort
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, Bot
from telegram.ext import (
    ApplicationBuilder,
    MessageHandler,
    CallbackQueryHandler,
    ContextTypes,
    filters,
)

nest_asyncio.apply()

BOT_TOKEN = os.getenv("BOT_TOKEN")
CHANNEL_ID = int(os.getenv("CHANNEL_ID"))
APP_URL = "https://telegram-bot-xq3r.onrender.com"  # آدرس وبهوک شما

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
            parse_mode="Markdown")
        return

    original, translated = map(str.strip, update.message.caption.split("|", 1))
    photo = update.message.photo[-1]
    file_id = photo.file_id

    short_id = shorten_file_id(file_id)
    translation_store[short_id] = translated
    save_translations(translation_store)

    await context.bot.send_photo(
        chat_id=CHANNEL_ID,
        photo=file_id,
        caption=original,
        reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("Translate", callback_data=f"translate_{short_id}")]])
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

app = Flask(__name__)
bot = Bot(token=BOT_TOKEN)
application = ApplicationBuilder().bot(bot).build()

# اضافه کردن هندلرها به اپلیکیشن
application.add_handler(MessageHandler(filters.PHOTO, handle_photo))
application.add_handler(CallbackQueryHandler(button_handler))

@app.route('/')
def home():
    return "ربات فعاله 🚀"

@app.route(f'/{BOT_TOKEN}', methods=['POST'])
def webhook_handler():
    if request.method == "POST":
        update = Update.de_json(request.get_json(force=True), bot)
        asyncio.run(application.process_update(update))
        return "ok"
    else:
        abort(403)

def set_webhook():
    webhook_url = f"{APP_URL}/{BOT_TOKEN}"
    success = bot.set_webhook(webhook_url)
    if success:
        print(f"Webhook set successfully to {webhook_url}")
    else:
        print("Failed to set webhook")

if __name__ == "__main__":
    set_webhook()
    app.run(host="0.0.0.0", port=8080)
