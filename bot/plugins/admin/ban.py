from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes
from bot.logger import get_logger
from bot.utils.decorators import group_only, admin_only, bot_admin_required, skip_old_updates
from bot.utils.parse import extract_user

logger = get_logger(__name__)


@skip_old_updates
@group_only
@admin_only
@bot_admin_required
async def ban(update: Update, context: ContextTypes.DEFAULT_TYPE):
    target = await extract_user(update)
    if not target:
        await update.effective_message.reply_text("Usage: /ban <reply|@user|id>")
        return

    user_id, name = target
    chat_id = update.effective_chat.id

    await context.bot.ban_chat_member(chat_id=chat_id, user_id=user_id)
    await update.effective_message.reply_text(f"🚫 {name} has been banned.")
    logger.info("BAN %s → %s (%s) in %s",
                update.effective_user.first_name, name, user_id,
                update.effective_chat.title)


@skip_old_updates
@group_only
@admin_only
@bot_admin_required
async def unban(update: Update, context: ContextTypes.DEFAULT_TYPE):
    target = await extract_user(update)
    if not target:
        await update.effective_message.reply_text("Usage: /unban <reply|@user|id>")
        return

    user_id, name = target
    chat_id = update.effective_chat.id

    await context.bot.unban_chat_member(chat_id=chat_id, user_id=user_id)
    await update.effective_message.reply_text(f"✅ {name} has been unbanned.")
    logger.info("UNBAN %s → %s (%s) in %s",
                update.effective_user.first_name, name, user_id,
                update.effective_chat.title)


def register(app: Application):
    app.add_handler(CommandHandler("ban", ban))
    app.add_handler(CommandHandler("unban", unban))
