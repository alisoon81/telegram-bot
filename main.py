import os
import asyncio
import nest_asyncio

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
ApplicationBuilder,
MessageHandler,
filters,
CallbackQueryHandler,
ContextTypes,
)
from telegram.constants import ParseMode

from db_postgres import db
from keep_alive import keep_alive

BOT_TOKEN = os.environ["BOT_TOKEN"]

CHANNEL_ID = int(
os.environ.get("CHANNEL_ID", "-1002443008163")
)

ADMIN_USER_ID = 7301301416

def is_authorized(update: Update) -> bool:
if not update.effective_user:
return False

```
return update.effective_user.id == ADMIN_USER_ID
```

async def handle_photo(
update: Update,
context: ContextTypes.DEFAULT_TYPE
):
if not update.message:
return

```
if not is_authorized(update):
    await update.message.reply_text(
        "⛔ شما اجازه استفاده از این ربات را ندارید."
    )
    return

if not update.message.caption or "|" not in update.message.caption:
    await update.message.reply_text(
        "❌ لطفاً کپشن عکس را به این صورت بنویس:\n\n"
        "متن انگلیسی | ترجمه فارسی",
        parse_mode=ParseMode.MARKDOWN
    )
    return

original, translated = map(
    str.strip,
    update.message.caption.split("|", 1)
)

if not original or not translated:
    await update.message.reply_text(
        "❌ متن انگلیسی و ترجمه فارسی نمی‌توانند خالی باشند."
    )
    return

keyboard = [[
    InlineKeyboardButton(
        "Translate",
        callback_data="translate|pending"
    )
]]

photo = update.message.photo[-1]
file_id = photo.file_id

try:
    sent_msg = await context.bot.send_photo(
        chat_id=CHANNEL_ID,
        photo=file_id,
        caption=original,
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

    msg_id = str(sent_msg.message_id)

    await db.save_translation(
        msg_id,
        translated
    )

    new_keyboard = [[
        InlineKeyboardButton(
            "Translate",
            callback_data=f"translate|{msg_id}"
        )
    ]]

    await sent_msg.edit_reply_markup(
        reply_markup=InlineKeyboardMarkup(new_keyboard)
    )

    await update.message.reply_text(
        "✅ پست با موفقیت در کانال منتشر شد."
    )

except Exception as e:
    print(f"❌ خطا هنگام انتشار پست: {e}")

    await update.message.reply_text(
        "❌ هنگام انتشار پست خطایی رخ داد."
    )
```

async def button_handler(
update: Update,
context: ContextTypes.DEFAULT_TYPE
):
query = update.callback_query

```
try:
    if not query or not query.data:
        return

    _, msg_id = query.data.split("|", 1)

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
            text="⏱ دکمه منقضی شده یا خطایی پیش آمده.",
            show_alert=True
        )
    except Exception:
        pass
```

async def main():
await db.connect()

```
app = (
    ApplicationBuilder()
    .token(BOT_TOKEN)
    .build()
)

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

await app.run_polling(
    close_loop=False
)
```

if **name** == "**main**":
keep_alive()

```
nest_asyncio.apply()

asyncio.get_event_loop().run_until_complete(
    main()
)
```
