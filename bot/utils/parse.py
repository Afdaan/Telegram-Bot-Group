import re
from datetime import timedelta
from telegram import Update
from telegram.constants import MessageEntityType
from telegram.error import BadRequest
from telegram.ext import ContextTypes
from bot.logger import get_logger
from bot.utils.user_cache import get_user_id_by_username
from bot.database.repo import Repository

logger = get_logger(__name__)

DURATION_PATTERN = re.compile(r"(\d+)\s*([mhd])", re.IGNORECASE)

DURATION_UNITS = {
    "m": "minutes",
    "h": "hours",
    "d": "days",
}


async def extract_user(update: Update) -> tuple[int, str] | None:
    message = update.effective_message

    if message.entities:
        text_mentions = message.parse_entities([MessageEntityType.TEXT_MENTION])
        for entity, _ in text_mentions.items():
            if entity.user:
                user = entity.user
                return user.id, user.first_name or user.username or str(user.id)

        for entity in message.entities:
            if entity.type in ("text_mention", MessageEntityType.TEXT_MENTION) and entity.user:
                user = entity.user
                if user and user.id:
                    return user.id, user.first_name or user.username or str(user.id)

        mentions = message.parse_entities([MessageEntityType.MENTION])
        for _, mention_text in mentions.items():
            username = (mention_text or "").lstrip("@").strip()
            if not username:
                continue

            cached_id = get_user_id_by_username(username)
            if cached_id:
                return cached_id, f"@{username}"
            
            db_user = await Repository.get_user_by_username(username)
            if db_user:
                return db_user.telegram_id, f"@{username}"

    if message.reply_to_message:
        reply_msg = message.reply_to_message
        has_topic = (
            reply_msg.forum_topic_created 
            or reply_msg.forum_topic_edited 
            or reply_msg.forum_topic_closed
            or getattr(reply_msg, 'is_topic_message', False)
        )
        
        if not has_topic:
            target = reply_msg.from_user
            if target and target.id and target.id != 0:
                return target.id, target.first_name or target.username or str(target.id)

    args = (message.text or message.caption or "").split()
    
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

    cached_id = get_user_id_by_username(identifier)
    if cached_id:
        return cached_id, f"@{identifier}"
    
    db_user = await Repository.get_user_by_username(identifier)
    if db_user:
        return db_user.telegram_id, f"@{identifier}"

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
