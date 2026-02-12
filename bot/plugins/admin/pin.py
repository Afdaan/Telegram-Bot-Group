from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes
from bot.logger import get_logger
from bot.utils.decorators import group_only, admin_only, bot_admin_required

logger = get_logger(__name__)


@group_only
@admin_only
@bot_admin_required
async def pin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.effective_message.reply_to_message:
        await update.effective_message.reply_text("Reply to a message to pin it.")
        return

    await context.bot.pin_chat_message(
        chat_id=update.effective_chat.id,
        message_id=update.effective_message.reply_to_message.message_id,
    )
    await update.effective_message.reply_text("📌 Message pinned.")
    logger.info("PIN %s in %s", update.effective_user.first_name, update.effective_chat.title)


@group_only
@admin_only
@bot_admin_required
async def unpin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_message.reply_to_message:
        await context.bot.unpin_chat_message(
            chat_id=update.effective_chat.id,
            message_id=update.effective_message.reply_to_message.message_id,
        )
    else:
        await context.bot.unpin_all_chat_messages(chat_id=update.effective_chat.id)

    await update.effective_message.reply_text("📌 Message(s) unpinned.")
    logger.info("UNPIN %s in %s", update.effective_user.first_name, update.effective_chat.title)


def register(app: Application):
    app.add_handler(CommandHandler("pin", pin))
    app.add_handler(CommandHandler("unpin", unpin))
