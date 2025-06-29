import json
import os
from keep_alive import keep_alive  # این رو اضافه کنید
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, Bot
from telegram.ext import ApplicationBuilder, MessageHandler, filters, CallbackQueryHandler, ContextTypes
from telegram.constants import ParseMode

BOT_TOKEN = "7045011878:AAFxYZtoUV7_-7x8uxYbx1lwEyBgW2oAUf0"
CHANNEL_ID = -1002443008163  # آیدی عددی کانال
TRANSLATION_FILE = "translations.json"

def load_translations():
    if not os.path.exists(TRANSLATION_FILE):
        return {}
    with open(TRANSLATION_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def save_translations(data):
    with open(TRANSLATION_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

translation_store = load_translations()

async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message.caption or "|" not in update.message.caption:
        await update.message.reply_text(
            "❌ لطفاً کپشن عکس رو به این صورت بنویس:\n`متن انگلیسی | ترجمه فارسی`",
            parse_mode=ParseMode.MARKDOWN
        )
        return

    original, translated = map(str.strip, update.message.caption.split("|", 1))

    keyboard = [
        [InlineKeyboardButton("Translate", callback_data="translate|pending")]
    ]

    photo = update.message.photo[-1]
    file_id = photo.file_id

    sent_msg = await context.bot.send_photo(
        chat_id=CHANNEL_ID,
        photo=file_id,
        caption=original,
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

    msg_id = str(sent_msg.message_id)

    translation_store[msg_id] = translated
    save_translations(translation_store)

    new_keyboard = [
        [InlineKeyboardButton("Translate", callback_data=f"translate|{msg_id}")]
    ]
    await sent_msg.edit_reply_markup(reply_markup=InlineKeyboardMarkup(new_keyboard))

    await update.message.reply_text("✅ پست در کانال منتشر شد.")

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    try:
        query_data = query.data
        if not query_data.startswith("translate|"):
            await query.answer("❌ درخواست نامعتبر بود.", show_alert=True)
            return

        _, msg_id = query_data.split("|", 1)
        translation = translation_store.get(msg_id, "❌ ترجمه‌ای یافت نشد.")
        await query.answer(text=translation, show_alert=True)

    except Exception as e:
        print(f"⚠️ خطا در پاسخ به دکمه: {e}")
        try:
            await query.answer(text="⏱ دکمه منقضی شده یا خطایی پیش اومده.", show_alert=True)
        except:
            pass

if __name__ == "__main__":
    bot = Bot(BOT_TOKEN)
    bot.delete_webhook()
    print("Webhook deleted")

    keep_alive()  # برای جلوگیری از خواب رفتن سرور (اگه لازم داری)
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(MessageHandler(filters.PHOTO, handle_photo))
    app.add_handler(CallbackQueryHandler(button_handler))

    print("✅ ربات آماده اجراست...")

    app.run_polling()
