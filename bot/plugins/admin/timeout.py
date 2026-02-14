from datetime import datetime
from telegram import Update, ChatPermissions
from telegram.ext import Application, CommandHandler, ContextTypes
from bot.logger import get_logger
from bot.utils.decorators import group_only, admin_only, bot_admin_required, skip_old_updates
from bot.utils.parse import extract_user, parse_duration, format_duration, check_target_not_admin

logger = get_logger(__name__)


@skip_old_updates
@group_only
@admin_only
@bot_admin_required
async def timeout(update: Update, context: ContextTypes.DEFAULT_TYPE):
    target = await extract_user(update)
    if not target:
        await update.effective_message.reply_text("Usage: /timeout <reply|@user|id> <duration: 30m/2h/1d>")
        return

    user_id, name = target

    if not await check_target_not_admin(update, context, user_id):
        return

    args = update.effective_message.text.split()
    duration_text = args[2] if len(args) >= 3 else (args[1] if update.effective_message.reply_to_message and len(args) >= 2 else None)

    if not duration_text:
        await update.effective_message.reply_text("Please specify a duration (e.g., 30m, 2h, 1d).")
        return

    duration = parse_duration(duration_text)
    if not duration:
        await update.effective_message.reply_text("Invalid duration format. Use: 30m, 2h, 1d")
        return

    chat_id = update.effective_chat.id
    until_date = datetime.utcnow() + duration

    restricted_permissions = ChatPermissions(
        can_send_messages=False,
        can_send_other_messages=False,
        can_add_web_page_previews=False,
        can_send_polls=False,
        can_change_info=False,
        can_invite_users=False,
        can_pin_messages=False,
    )

    await context.bot.restrict_chat_member(
        chat_id=chat_id,
        user_id=user_id,
        permissions=restricted_permissions,
        until_date=until_date,
    )

    await update.effective_message.reply_text(
        f"⏱ {name} has been timed out for {format_duration(duration)}."
    )
    logger.info("TIMEOUT %s → %s (%s) in %s for %s",
                update.effective_user.first_name, name, user_id,
                update.effective_chat.title, format_duration(duration))


def register(app: Application):
    app.add_handler(CommandHandler("timeout", timeout))
