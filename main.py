import os
import json
import hashlib
from flask import Flask, request, Response
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CallbackQueryHandler, ContextTypes, MessageHandler, filters
import asyncio

BOT_TOKEN = os.getenv("BOT_TOKEN")
CHANNEL_ID = int(os.getenv("CHANNEL_ID"))
APP_URL = os.getenv("https://telegram-bot-xq3r.onrender.com")  # آدرس عمومی که وبهوک رو روش ست می‌کنی

TRANSLATION_FILE = "translations.json"

# بارگذاری و ذخیره ترجمه‌ها
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

# هندلر دریافت عکس با کپشن
async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message.caption or "|" not in update.message.caption:
        await update.message.reply_text(
            "❌ لطفاً کپشن عکس رو به این صورت بنویس:\n`متن انگلیسی | ترجمه فارسی`",
            parse_mode="Markdown"
        )
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
        reply_markup=InlineKeyboardMarkup([[
            InlineKeyboardButton("Translate", callback_data=f"translate_{short_id}")
        ]])
    )

    await update.message.reply_text("✅ پست در کانال منتشر شد.")

# هندلر دکمه ترجمه
async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    data = query.data
    if data.startswith("translate_"):
        short_id = data.split("_", 1)[1]
        translation = translation_store.get(short_id, "❌ ترجمه‌ای یافت نشد.")
        await query.answer(text=translation, show_alert=True)
    else:
        await query.answer()

# ساخت اپلیکیشن بات
application = ApplicationBuilder().token(BOT_TOKEN).build()
application.add_handler(MessageHandler(filters.PHOTO, handle_photo))
application.add_handler(CallbackQueryHandler(button_handler))

# Flask app برای وبهوک
flask_app = Flask(__name__)

@flask_app.route('/')
def home():
    return "ربات فعال است 🚀"

@flask_app.route(f'/{BOT_TOKEN}', methods=["POST"])
def webhook():
    json_update = request.get_json(force=True)
    update = Update.de_json(json_update, application.bot)
    asyncio.run(application.update_queue.put(update))
    return Response("ok", status=200)

if __name__ == "__main__":
    # تنظیم وبهوک روی آدرس عمومی + توکن بات
    import telegram
    bot = telegram.Bot(token=BOT_TOKEN)
    webhook_url = f"{APP_URL}/{BOT_TOKEN}"
    bot.delete_webhook()
    bot.set_webhook(url=webhook_url)

    print(f"Webhook set to: {webhook_url}")

    flask_app.run(host="0.0.0.0", port=8080)
