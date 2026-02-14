from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes
from bot.logger import get_logger
from bot.utils.decorators import group_only, admin_only, bot_admin_required, skip_old_updates

logger = get_logger(__name__)

MAX_PURGE = 200


async def _batch_delete(context, chat_id: int, message_ids: list[int]):
    batch_size = 100
    for i in range(0, len(message_ids), batch_size):
        batch = message_ids[i:i + batch_size]
        try:
            await context.bot.delete_messages(chat_id=chat_id, message_ids=batch)
        except Exception:
            for mid in batch:
                try:
                    await context.bot.delete_message(chat_id=chat_id, message_id=mid)
                except Exception:
                    continue


@skip_old_updates
@group_only
@admin_only
@bot_admin_required
async def purge(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    cmd_msg_id = update.effective_message.message_id
    reply = update.effective_message.reply_to_message

    if reply:
        start_id = reply.message_id
        count = cmd_msg_id - start_id + 1
        if count > MAX_PURGE:
            await update.effective_message.reply_text(f"Too many messages. Maximum is {MAX_PURGE}.")
            return
        message_ids = list(range(start_id, cmd_msg_id + 1))

    else:
        args = update.effective_message.text.split()
        if len(args) < 2 or not args[1].isdigit():
            await update.effective_message.reply_text(
                "Usage:\n"
                "• Reply to a message with /purge to delete from that point\n"
                "• /purge <number> to delete last N messages"
            )
            return
        count = int(args[1])
        if count < 1 or count > MAX_PURGE:
            await update.effective_message.reply_text(f"Please specify a number between 1 and {MAX_PURGE}.")
            return
        message_ids = list(range(cmd_msg_id, cmd_msg_id - count - 1, -1))

    await _batch_delete(context, chat_id, message_ids)
    logger.info("PURGE %s deleted %d messages in %s",
                update.effective_user.first_name, len(message_ids),
                update.effective_chat.title)


def register(app: Application):
    app.add_handler(CommandHandler("purge", purge))
