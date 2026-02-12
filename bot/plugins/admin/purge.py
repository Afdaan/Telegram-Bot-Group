from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes
from bot.logger import get_logger
from bot.utils.decorators import group_only, admin_only, bot_admin_required

logger = get_logger(__name__)


@group_only
@admin_only
@bot_admin_required
async def purge(update: Update, context: ContextTypes.DEFAULT_TYPE):
    args = update.effective_message.text.split()
    if len(args) < 2 or not args[1].isdigit():
        await update.effective_message.reply_text("Usage: /purge <number>")
        return

    count = int(args[1])
    if count < 1 or count > 100:
        await update.effective_message.reply_text("Please specify a number between 1 and 100.")
        return

    chat_id = update.effective_chat.id
    message_id = update.effective_message.message_id

    message_ids = list(range(message_id, message_id - count - 1, -1))

    try:
        await context.bot.delete_messages(chat_id=chat_id, message_ids=message_ids)
    except Exception:
        for mid in message_ids:
            try:
                await context.bot.delete_message(chat_id=chat_id, message_id=mid)
            except Exception:
                continue

    logger.info("PURGE %s deleted %d messages in %s",
                update.effective_user.first_name, count,
                update.effective_chat.title)


def register(app: Application):
    app.add_handler(CommandHandler("purge", purge))
