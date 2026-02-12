import re
from datetime import timedelta
from telegram import Message, Update


DURATION_PATTERN = re.compile(r"(\d+)\s*([mhd])", re.IGNORECASE)

DURATION_UNITS = {
    "m": "minutes",
    "h": "hours",
    "d": "days",
}


async def extract_user(update: Update) -> tuple[int, str] | None:
    message = update.effective_message

    if message.reply_to_message:
        target = message.reply_to_message.from_user
        return target.id, target.first_name or target.username or str(target.id)

    args = message.text.split()
    if len(args) < 2:
        return None

    identifier = args[1]

    if identifier.startswith("@"):
        identifier = identifier[1:]

    if identifier.isdigit():
        return int(identifier), identifier

    return None


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
