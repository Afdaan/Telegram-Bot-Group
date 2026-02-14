from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes
from bot.database.repo import Repository
from bot.logger import get_logger
from bot.utils.decorators import group_only, admin_only, bot_admin_required, skip_old_updates

logger = get_logger(__name__)

DEFAULT_SLOWMODE = 30


@skip_old_updates
@group_only
@admin_only
@bot_admin_required
async def slowmode(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    args = update.effective_message.text.split()

    if len(args) < 2:
        settings = await Repository.get_or_create_settings(chat_id)
        status = "✅ Enabled" if settings.slowmode_seconds > 0 else "❌ Disabled"
        await update.effective_message.reply_text(
            f"🐢 Slowmode settings:\n"
            f"  Status: {status}\n"
            f"  Delay: {settings.slowmode_seconds} seconds\n\n"
            f"Usage:\n"
            f"  /slowmode on - Enable slowmode\n"
            f"  /slowmode off - Disable slowmode\n"
            f"  /slowmode <seconds> - Set custom delay (0-3600)"
        )
        return

    action = args[1].lower()
    await Repository.upsert_group(chat_id, title=update.effective_chat.title)

    if action in ("on", "enable"):
        settings = await Repository.get_or_create_settings(chat_id)
        seconds = settings.slowmode_seconds if settings.slowmode_seconds > 0 else DEFAULT_SLOWMODE
        await context.bot.set_chat_slow_mode_delay(chat_id=chat_id, slow_mode_delay=seconds)
        await Repository.update_settings(chat_id, slowmode_seconds=seconds)
        await update.effective_message.reply_text(f"🐢 Slowmode enabled: {seconds} second(s).")
        logger.info("SLOWMODE %s enabled %ds in %s",
                    update.effective_user.first_name, seconds, update.effective_chat.title)
        return

    if action in ("off", "disable"):
        await context.bot.set_chat_slow_mode_delay(chat_id=chat_id, slow_mode_delay=0)
        await Repository.update_settings(chat_id, slowmode_seconds=0)
        await update.effective_message.reply_text("🐢 Slowmode disabled.")
        logger.info("SLOWMODE %s disabled in %s",
                    update.effective_user.first_name, update.effective_chat.title)
        return

    if not action.isdigit():
        await update.effective_message.reply_text("Usage: /slowmode <on|off|seconds>")
        return

    seconds = int(action)
    if seconds < 0 or seconds > 3600:
        await update.effective_message.reply_text("Slowmode must be between 0 and 3600 seconds.")
        return

    await context.bot.set_chat_slow_mode_delay(chat_id=chat_id, slow_mode_delay=seconds)
    await Repository.update_settings(chat_id, slowmode_seconds=seconds)

    if seconds == 0:
        await update.effective_message.reply_text("🐢 Slowmode disabled.")
    else:
        await update.effective_message.reply_text(f"🐢 Slowmode set to {seconds} second(s).")

    logger.info("SLOWMODE %s set to %ds in %s",
                update.effective_user.first_name, seconds, update.effective_chat.title)


def register(app: Application):
    app.add_handler(CommandHandler("slowmode", slowmode))
