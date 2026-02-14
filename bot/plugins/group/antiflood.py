import time
from collections import defaultdict
from telegram import Update, ChatPermissions
from telegram.error import BadRequest
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from bot.database.repo import Repository
from bot.logger import get_logger
from bot.utils.decorators import group_only, admin_only

logger = get_logger(__name__)

flood_tracker: dict[str, list[float]] = defaultdict(list)

STALE_THRESHOLD = 60
MIN_FLOOD_LIMIT = 3


def _tracker_key(chat_id: int, user_id: int) -> str:
    return f"{chat_id}:{user_id}"


async def check_flood(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.effective_message or not update.effective_user:
        return
    if update.effective_chat.type not in ("group", "supergroup"):
        return

    msg_time = update.effective_message.date.timestamp()
    now = time.time()

    if now - msg_time > STALE_THRESHOLD:
        return

    chat_id = update.effective_chat.id
    user_id = update.effective_user.id

    member = await context.bot.get_chat_member(chat_id, user_id)
    if member.status in ("administrator", "creator"):
        flood_tracker.pop(_tracker_key(chat_id, user_id), None)
        return

    settings = await Repository.get_or_create_settings(chat_id)
    if settings.antiflood_limit <= 0:
        return

    key = _tracker_key(chat_id, user_id)
    cutoff = msg_time - settings.antiflood_time

    flood_tracker[key] = [t for t in flood_tracker[key] if t > cutoff]
    flood_tracker[key].append(msg_time)

    if len(flood_tracker[key]) >= settings.antiflood_limit:
        flood_tracker[key].clear()

        try:
            await context.bot.restrict_chat_member(
                chat_id=chat_id,
                user_id=user_id,
                permissions=ChatPermissions(can_send_messages=False),
            )
            await update.effective_message.reply_text(
                f"🚫 {update.effective_user.first_name} has been muted for flooding."
            )
            logger.info("ANTIFLOOD muted %s (%s) in %s",
                        update.effective_user.first_name, user_id,
                        update.effective_chat.title)
        except BadRequest:
            await Repository.update_settings(chat_id, antiflood_limit=0)
            await update.effective_message.reply_text(
                "⚠️ I don't have permission to restrict users. Anti-flood has been auto-disabled."
            )
            logger.warning("ANTIFLOOD auto-disabled in %s, no restrict permissions",
                           update.effective_chat.title)


@group_only
async def flood(update: Update, context: ContextTypes.DEFAULT_TYPE):
    settings = await Repository.get_or_create_settings(update.effective_chat.id)
    if settings.antiflood_limit <= 0:
        await update.effective_message.reply_text("🌊 Anti-flood is currently disabled.")
    else:
        await update.effective_message.reply_text(
            f"🌊 Anti-flood is active: {settings.antiflood_limit} messages "
            f"in {settings.antiflood_time} seconds."
        )


@group_only
@admin_only
async def antiflood(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    args = update.effective_message.text.split()

    if len(args) < 2:
        settings = await Repository.get_or_create_settings(chat_id)
        status = "✅ Enabled" if settings.antiflood_limit > 0 else "❌ Disabled"
        await update.effective_message.reply_text(
            f"🌊 Anti-flood settings:\n"
            f"  Status: {status}\n"
            f"  Limit: {settings.antiflood_limit} messages\n"
            f"  Window: {settings.antiflood_time} seconds\n\n"
            f"Usage:\n"
            f"  /antiflood on - Enable anti-flood\n"
            f"  /antiflood off - Disable anti-flood\n"
            f"  /antiflood <limit> [window] - Set custom values (min: {MIN_FLOOD_LIMIT})"
        )
        return

    action = args[1].lower()
    await Repository.upsert_group(chat_id, title=update.effective_chat.title)

    if action in ("on", "enable"):
        settings = await Repository.get_or_create_settings(chat_id)
        limit = settings.antiflood_limit if settings.antiflood_limit >= MIN_FLOOD_LIMIT else 5
        window = settings.antiflood_time if settings.antiflood_time > 0 else 10
        await Repository.update_settings(chat_id, antiflood_limit=limit, antiflood_time=window)
        await update.effective_message.reply_text(
            f"🌊 Anti-flood enabled: {limit} messages in {window} seconds."
        )
        return

    if action in ("off", "disable", "no", "0"):
        await Repository.update_settings(chat_id, antiflood_limit=0)
        await update.effective_message.reply_text("🌊 Anti-flood disabled.")
        return

    if not action.isdigit():
        await update.effective_message.reply_text("Usage: /antiflood <on|off|number>")
        return

    limit = int(action)
    window = int(args[2]) if len(args) > 2 and args[2].isdigit() else 10

    if limit <= 0:
        await Repository.update_settings(chat_id, antiflood_limit=0)
        await update.effective_message.reply_text("🌊 Anti-flood disabled.")
        return

    if limit < MIN_FLOOD_LIMIT:
        await update.effective_message.reply_text(
            f"⚠️ Anti-flood limit must be at least {MIN_FLOOD_LIMIT}, or 0 to disable."
        )
        return

    await Repository.update_settings(chat_id, antiflood_limit=limit, antiflood_time=window)
    await update.effective_message.reply_text(
        f"🌊 Anti-flood set: {limit} messages in {window} seconds."
    )


def register(app: Application):
    app.add_handler(MessageHandler(
        filters.ALL & ~filters.COMMAND & ~filters.StatusUpdate.ALL,
        check_flood,
    ), group=-1)
    app.add_handler(CommandHandler("flood", flood))
    app.add_handler(CommandHandler("antiflood", antiflood))
