import re
from datetime import timedelta
from telegram import Update
from telegram.error import BadRequest
from telegram.ext import ContextTypes


DURATION_PATTERN = re.compile(r"(\d+)\s*([mhd])", re.IGNORECASE)

DURATION_UNITS = {
    "m": "minutes",
    "h": "hours",
    "d": "days",
}


async def extract_user(update: Update) -> tuple[int, str] | None:
    message = update.effective_message

    if message.entities:
        for entity in message.entities:
            if entity.type == "text_mention" and entity.user:
                user = entity.user
                if user and user.id:
                    return user.id, user.first_name or user.username or str(user.id)

            if entity.type == "mention":
                start = entity.offset
                end = entity.offset + entity.length
                mention_text = message.text[start:end]
                username = mention_text.lstrip('@')
                
                try:
                    chat = await message.get_bot().get_chat(f"@{username}")
                    if chat and chat.id:
                        return chat.id, chat.first_name or chat.username or str(chat.id)
                except (BadRequest, Exception) as e:
                    pass

    if message.reply_to_message:
        reply_msg = message.reply_to_message
        if not reply_msg.forum_topic_created and not reply_msg.forum_topic_edited and not reply_msg.forum_topic_closed:
            target = reply_msg.from_user
            if target and target.id:
                return target.id, target.first_name or target.username or str(target.id)

    args = message.text.split()
    if len(args) < 2:
        return None

    identifier = args[1].strip()

    if identifier.startswith("@"):
        identifier = identifier[1:]

    if identifier.isdigit():
        user_id = int(identifier)
        if user_id > 0:
            return user_id, str(user_id)
        return None

    try:
        chat = await message.get_bot().get_chat(f"@{identifier}")
        if chat and chat.id:
            return chat.id, chat.first_name or chat.username or str(chat.id)
    except (BadRequest, Exception) as e:
        pass

    return None


async def check_target_not_admin(
    update: Update, context: ContextTypes.DEFAULT_TYPE, user_id: int
) -> bool:
    chat_id = update.effective_chat.id
    member = await context.bot.get_chat_member(chat_id, user_id)
    if member.status in ("administrator", "creator"):
        await update.effective_message.reply_text("⚠️ Cannot perform this action on an admin.")
        return False
    return True


def parse_duration(text: str) -> timedelta | None:
    match = DURATION_PATTERN.search(text)
    if not match:
        return None

    amount = int(match.group(1))
    unit = match.group(2).lower()

    return timedelta(**{DURATION_UNITS[unit]: amount})


def format_duration(td: timedelta) -> str:
    total_seconds = int(td.total_seconds())

    if total_seconds >= 86400:
        return f"{total_seconds // 86400} day(s)"
    if total_seconds >= 3600:
        return f"{total_seconds // 3600} hour(s)"
    return f"{total_seconds // 60} minute(s)"
