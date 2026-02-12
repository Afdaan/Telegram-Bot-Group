from datetime import datetime, timedelta
from telegram import Update, ChatPermissions
from telegram.ext import Application, CommandHandler, ContextTypes
from bot.logger import get_logger
from bot.utils.decorators import group_only, admin_only, bot_admin_required
from bot.utils.parse import extract_user, parse_duration, format_duration

logger = get_logger(__name__)


@group_only
@admin_only
@bot_admin_required
async def mute(update: Update, context: ContextTypes.DEFAULT_TYPE):
    target = await extract_user(update)
    if not target:
        await update.effective_message.reply_text("Usage: /mute <reply|@user|id> [duration: 30m/2h/1d]")
        return

    user_id, name = target
    chat_id = update.effective_chat.id

    duration = None
    args = update.effective_message.text.split()
    if len(args) >= 3:
        duration = parse_duration(args[2])
    elif len(args) >= 2 and update.effective_message.reply_to_message:
        duration = parse_duration(args[1])

    permissions = ChatPermissions(can_send_messages=False)
    until_date = datetime.utcnow() + duration if duration else None

    await context.bot.restrict_chat_member(
        chat_id=chat_id,
        user_id=user_id,
        permissions=permissions,
        until_date=until_date,
    )

    duration_text = f" for {format_duration(duration)}" if duration else ""
    await update.effective_message.reply_text(f"🔇 {name} has been muted{duration_text}.")
    logger.info("MUTE %s → %s (%s) in %s%s",
                update.effective_user.first_name, name, user_id,
                update.effective_chat.title, duration_text)


@group_only
@admin_only
@bot_admin_required
async def unmute(update: Update, context: ContextTypes.DEFAULT_TYPE):
    target = await extract_user(update)
    if not target:
        await update.effective_message.reply_text("Usage: /unmute <reply|@user|id>")
        return

    user_id, name = target
    chat_id = update.effective_chat.id

    permissions = ChatPermissions(
        can_send_messages=True,
        can_send_other_messages=True,
        can_add_web_page_previews=True,
        can_send_polls=True,
        can_invite_users=True,
    )

    await context.bot.restrict_chat_member(
        chat_id=chat_id,
        user_id=user_id,
        permissions=permissions,
    )

    await update.effective_message.reply_text(f"🔊 {name} has been unmuted.")
    logger.info("UNMUTE %s → %s (%s) in %s",
                update.effective_user.first_name, name, user_id,
                update.effective_chat.title)


def register(app: Application):
    app.add_handler(CommandHandler("mute", mute))
    app.add_handler(CommandHandler("unmute", unmute))
