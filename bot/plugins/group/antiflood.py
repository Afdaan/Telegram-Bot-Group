import time
from collections import defaultdict
from telegram import Update, ChatPermissions
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from bot.database.repo import Repository
from bot.logger import get_logger
from bot.utils.decorators import group_only, admin_only

logger = get_logger(__name__)

flood_tracker: dict[str, list[float]] = defaultdict(list)


def _tracker_key(chat_id: int, user_id: int) -> str:
    return f"{chat_id}:{user_id}"


async def check_flood(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.effective_message or not update.effective_user:
        return
    if update.effective_chat.type not in ("group", "supergroup"):
        return

    chat_id = update.effective_chat.id
    user_id = update.effective_user.id

    member = await context.bot.get_chat_member(chat_id, user_id)
    if member.status in ("administrator", "creator"):
        return

    settings = await Repository.get_or_create_settings(chat_id)
    if settings.antiflood_limit <= 0:
        return

    key = _tracker_key(chat_id, user_id)
    now = time.time()
    cutoff = now - settings.antiflood_time

    flood_tracker[key] = [t for t in flood_tracker[key] if t > cutoff]
    flood_tracker[key].append(now)

    if len(flood_tracker[key]) >= settings.antiflood_limit:
        flood_tracker[key].clear()

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


@group_only
@admin_only
async def antiflood(update: Update, context: ContextTypes.DEFAULT_TYPE):
    args = update.effective_message.text.split()
    if len(args) < 2:
        settings = await Repository.get_or_create_settings(update.effective_chat.id)
        await update.effective_message.reply_text(
            f"🌊 Anti-flood settings:\n"
            f"  Limit: {settings.antiflood_limit} messages\n"
            f"  Window: {settings.antiflood_time} seconds\n\n"
            f"Usage: /antiflood <limit> [window_seconds]"
        )
        return

    limit = int(args[1]) if args[1].isdigit() else 0
    window = int(args[2]) if len(args) > 2 and args[2].isdigit() else 10

    chat_id = update.effective_chat.id
    await Repository.upsert_group(chat_id, title=update.effective_chat.title)
    await Repository.update_settings(chat_id, antiflood_limit=limit, antiflood_time=window)

    if limit <= 0:
        await update.effective_message.reply_text("🌊 Anti-flood disabled.")
    else:
        await update.effective_message.reply_text(
            f"🌊 Anti-flood set: {limit} messages in {window} seconds."
        )


def register(app: Application):
    app.add_handler(MessageHandler(
        filters.ALL & ~filters.COMMAND & ~filters.StatusUpdate.ALL,
        check_flood,
    ), group=-1)
    app.add_handler(CommandHandler("antiflood", antiflood))
