import os
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, MessageHandler, filters, CallbackQueryHandler, ContextTypes
from telegram.constants import ParseMode
import asyncio
from db_postgres import db
from keep_alive import keep_alive

BOT_TOKEN = os.environ.get("BOT_TOKEN", "7045011878:AAFxYZtoUV7_-7x8uxYbx1lwEyBgW2oAUf0")
CHANNEL_ID = int(os.environ.get("CHANNEL_ID", "-1002443008163"))


async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message.caption or "|" not in update.message.caption:
        await update.message.reply_text(
            "❌ لطفاً کپشن عکس رو به این صورت بنویس:\n`متن انگلیسی | ترجمه فارسی`",
            parse_mode=ParseMode.MARKDOWN
        )
        return

    original, translated = map(str.strip, update.message.caption.split("|", 1))

    keyboard = [[InlineKeyboardButton("Translate", callback_data="translate|pending")]]
    photo = update.message.photo[-1]
    file_id = photo.file_id

    sent_msg = await context.bot.send_photo(
        chat_id=CHANNEL_ID,
        photo=file_id,
        caption=original,
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

    msg_id = str(sent_msg.message_id)
    await db.save_translation(msg_id, translated)

    new_keyboard = [[InlineKeyboardButton("Translate", callback_data=f"translate|{msg_id}")]]
    await sent_msg.edit_reply_markup(reply_markup=InlineKeyboardMarkup(new_keyboard))
    await update.message.reply_text("✅ پست در کانال منتشر شد.")


async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    try:
        _, msg_id = query.data.split("|", 1)
        translation = await db.get_translation(msg_id)
        if not translation:
            translation = "❌ ترجمه‌ای یافت نشد."
        await query.answer(text=translation, show_alert=True)
    except Exception as e:
        print(f"⚠️ خطا در پاسخ به دکمه: {e}")
        try:
            await query.answer(text="⏱ دکمه منقضی شده یا خطایی پیش اومده.", show_alert=True)
        except:
            pass


async def main():
    await db.connect()

    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(MessageHandler(filters.PHOTO, handle_photo))
    app.add_handler(CallbackQueryHandler(button_handler))

    print("✅ ربات آماده اجراست...")
    await app.run_polling(close_loop=False)


if __name__ == "__main__":
    keep_alive()

    import nest_asyncio
    nest_asyncio.apply()

    asyncio.get_event_loop().run_until_complete(main())
