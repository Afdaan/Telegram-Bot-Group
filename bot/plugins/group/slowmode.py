from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes
from bot.database.repo import Repository
from bot.logger import get_logger
from bot.utils.decorators import group_only, admin_only, bot_admin_required

logger = get_logger(__name__)


@group_only
@admin_only
@bot_admin_required
async def slowmode(update: Update, context: ContextTypes.DEFAULT_TYPE):
    args = update.effective_message.text.split()
    if len(args) < 2 or not args[1].isdigit():
        await update.effective_message.reply_text("Usage: /slowmode <seconds> (0 to disable)")
        return

    seconds = int(args[1])
    if seconds < 0 or seconds > 3600:
        await update.effective_message.reply_text("Slowmode must be between 0 and 3600 seconds.")
        return

    chat_id = update.effective_chat.id

    await context.bot.set_chat_permissions(
        chat_id=chat_id,
        permissions=update.effective_chat.permissions,
    )
    await context.bot.set_chat_slow_mode_delay(chat_id=chat_id, slow_mode_delay=seconds)

    await Repository.upsert_group(chat_id, title=update.effective_chat.title)
    await Repository.update_settings(chat_id, slowmode_seconds=seconds)

    if seconds == 0:
        await update.effective_message.reply_text("🐢 Slowmode disabled.")
    else:
        await update.effective_message.reply_text(f"🐢 Slowmode set to {seconds} second(s).")

    logger.info("SLOWMODE %s set to %ds in %s",
                update.effective_user.first_name, seconds, update.effective_chat.title)


def register(app: Application):
    app.add_handler(CommandHandler("slowmode", slowmode))
