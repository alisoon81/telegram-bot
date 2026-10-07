import os
import asyncio
import nest_asyncio

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, MessageHandler, filters, CallbackQueryHandler, ContextTypes
from telegram.constants import ParseMode

from db_postgres import db
from keep_alive import keep_alive

BOT_TOKEN = os.environ["BOT_TOKEN"]
CHANNEL_ID = int(os.environ.get("CHANNEL_ID", "-1002443008163"))
ADMIN_USER_ID = 7301301416

def is_authorized(update: Update) -> bool:
return (
update.effective_user is not None
and update.effective_user.id == ADMIN_USER_ID
)

async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
if update.message is None:
return

if not is_authorized(update):
    await update.message.reply_text(
        "⛔ شما اجازه استفاده از این ربات را ندارید."
    )
    return

caption = update.message.caption

if not caption or "|" not in caption:
    await update.message.reply_text(
        "❌ لطفاً کپشن عکس را این‌طور بنویس:\n\n"
        "متن انگلیسی | ترجمه فارسی",
        parse_mode=ParseMode.MARKDOWN
    )
    return

original, translated = map(str.strip, caption.split("|", 1))

if not original or not translated:
    await update.message.reply_text(
        "❌ متن انگلیسی و ترجمه فارسی نمی‌توانند خالی باشند."
    )
    return

try:
    photo = update.message.photo[-1]
    file_id = photo.file_id

    temporary_keyboard = InlineKeyboardMarkup([
        [
            InlineKeyboardButton(
                "Translate",
                callback_data="translate|pending"
            )
        ]
    ])

    sent_msg = await context.bot.send_photo(
        chat_id=CHANNEL_ID,
        photo=file_id,
        caption=original,
        reply_markup=temporary_keyboard
    )

    msg_id = str(sent_msg.message_id)

    await db.save_translation(
        msg_id,
        translated
    )

    final_keyboard = InlineKeyboardMarkup([
        [
            InlineKeyboardButton(
                "Translate",
                callback_data=f"translate|{msg_id}"
            )
        ]
    ])

    await sent_msg.edit_reply_markup(
        reply_markup=final_keyboard
    )

    await update.message.reply_text(
        "✅ پست با موفقیت در کانال منتشر شد."
    )

except Exception as e:
    print(f"❌ خطا هنگام انتشار پست: {e}")

    await update.message.reply_text(
        "❌ هنگام انتشار پست خطایی رخ داد."
    )

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
query = update.callback_query

if query is None:
    return

try:
    if not query.data:
        return

    parts = query.data.split("|", 1)

    if len(parts) != 2:
        await query.answer(
            "❌ اطلاعات دکمه نامعتبر است.",
            show_alert=True
        )
        return

    _, msg_id = parts

    translation = await db.get_translation(msg_id)

    if not translation:
        translation = "❌ ترجمه‌ای یافت نشد."

    await query.answer(
        text=translation,
        show_alert=True
    )

except Exception as e:
    print(f"⚠️ خطا در پاسخ به دکمه: {e}")

    try:
        await query.answer(
            text="⏱ خطایی در دریافت ترجمه رخ داد.",
            show_alert=True
        )
    except Exception:
        pass

async def main():
await db.connect()

app = ApplicationBuilder().token(BOT_TOKEN).build()

app.add_handler(
    MessageHandler(
        filters.PHOTO,
        handle_photo
    )
)

app.add_handler(
    CallbackQueryHandler(
        button_handler
    )
)

print("✅ ربات آماده اجراست...")

await app.run_polling(close_loop=False)

if name == "main":
keep_alive()

nest_asyncio.apply()

asyncio.get_event_loop().run_until_complete(main())
