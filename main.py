from flask import Flask, request
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
import os
import asyncio
import nest_asyncio

nest_asyncio.apply()

# گرفتن توکن از محیط
BOT_TOKEN = os.environ.get("BOT_TOKEN")
WEBHOOK_PATH = "/webhook"
WEBHOOK_URL = f"https://telegram-bot-xq3r.onrender.com{WEBHOOK_PATH}"

# Flask app
flask_app = Flask(__name__)

# ایجاد ربات
application = ApplicationBuilder().token(BOT_TOKEN).build()

# هندلر دستور /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("سلام! من با موفقیت راه‌اندازی شدم.")

application.add_handler(CommandHandler("start", start))

# تنظیم webhook بعد از اولین درخواست
@flask_app.before_first_request
def setup():
    asyncio.get_event_loop().create_task(application.bot.set_webhook(WEBHOOK_URL))

# مسیر دریافت پیام‌ها از Telegram
@flask_app.route(WEBHOOK_PATH, methods=["POST"])
def receive_update():
    update = Update.de_json(request.get_json(force=True), application.bot)
    application.update_queue.put_nowait(update)
    return "ok"

# اجرای سرور Flask
if __name__ == "__main__":
    flask_app.run(host="0.0.0.0", port=10000)
