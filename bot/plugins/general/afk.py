import time
from telegram import Update, MessageEntity
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from bot.logger import get_logger

logger = get_logger(__name__)

afk_users: dict[int, dict] = {}

AFK_GROUP = 7
AFK_REPLY_GROUP = 8


async def afk(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.effective_user:
        return

    user_id = update.effective_user.id
    args = update.effective_message.text.split(None, 1)
    reason = args[1] if len(args) >= 2 else ""

    afk_users[user_id] = {
        "reason": reason,
        "time": time.time(),
    }

    await update.effective_message.reply_text(
        f"💤 {update.effective_user.first_name} is now AFK!"
    )


async def no_longer_afk(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.effective_user or not update.effective_message:
        return

    user_id = update.effective_user.id

    if user_id in afk_users:
        afk_data = afk_users.pop(user_id)
        elapsed = int(time.time() - afk_data["time"])

        if elapsed < 60:
            duration = f"{elapsed}s"
        elif elapsed < 3600:
            duration = f"{elapsed // 60}m"
        else:
            duration = f"{elapsed // 3600}h {(elapsed % 3600) // 60}m"

        await update.effective_message.reply_text(
            f"👋 {update.effective_user.first_name} is back! Was away for {duration}."
        )


async def reply_afk(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.effective_message:
        return

    message = update.effective_message

    if message.reply_to_message and message.reply_to_message.from_user:
        replied_user = message.reply_to_message.from_user
        if replied_user.id in afk_users:
            afk_data = afk_users[replied_user.id]
            text = f"💤 {replied_user.first_name} is AFK."
            if afk_data["reason"]:
                text += f"\nReason: {afk_data['reason']}"
            await message.reply_text(text)
            return

    if not message.entities:
        return

    for entity in message.entities:
        user_id = None
        name = None

        if entity.type == MessageEntity.TEXT_MENTION and entity.user:
            user_id = entity.user.id
            name = entity.user.first_name
        elif entity.type == MessageEntity.MENTION:
            username = message.text[entity.offset + 1:entity.offset + entity.length]
            for uid, data in afk_users.items():
                try:
                    member = await context.bot.get_chat(uid)
                    if member.username and member.username.lower() == username.lower():
                        user_id = uid
                        name = member.first_name
                        break
                except Exception:
                    continue

        if user_id and user_id in afk_users:
            afk_data = afk_users[user_id]
            text = f"💤 {name} is AFK."
            if afk_data["reason"]:
                text += f"\nReason: {afk_data['reason']}"
            await message.reply_text(text)


def register(app: Application):
    app.add_handler(CommandHandler("afk", afk), group=AFK_GROUP)
    app.add_handler(MessageHandler(
        filters.Regex(r"(?i)^brb") & filters.ChatType.GROUPS,
        afk,
    ), group=AFK_GROUP)
    app.add_handler(MessageHandler(
        filters.ALL & ~filters.COMMAND & filters.ChatType.GROUPS,
        no_longer_afk,
    ), group=AFK_GROUP)
    app.add_handler(MessageHandler(
        (filters.Entity(MessageEntity.MENTION)
         | filters.Entity(MessageEntity.TEXT_MENTION)
         | filters.REPLY) & filters.ChatType.GROUPS,
        reply_afk,
    ), group=AFK_REPLY_GROUP)
