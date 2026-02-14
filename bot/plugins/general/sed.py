import re
from telegram import Update, constants
from telegram.ext import Application, MessageHandler, filters, ContextTypes
from bot.logger import get_logger

logger = get_logger(__name__)

DELIMITERS = "/:|_"
SED_PATTERN = re.compile(r"^s([/:|_])(.+?)\1(.*?)(?:\1([ig]*))?$", re.DOTALL)


def parse_sed(text: str):
    match = SED_PATTERN.match(text)
    if not match:
        return None

    find = match.group(2)
    replace = match.group(3)
    flags = match.group(4) or ""

    return find, replace, flags.lower()


async def sed(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.effective_message or not update.effective_message.reply_to_message:
        return

    message = update.effective_message
    reply = message.reply_to_message

    original = reply.text or reply.caption
    if not original:
        return

    result = parse_sed(message.text)
    if not result:
        return

    find, replace, flags = result

    if not find:
        await message.reply_text("You're trying to replace... nothing?")
        return

    try:
        re_flags = re.IGNORECASE if "i" in flags else 0
        count = 0 if "g" in flags else 1

        check = re.fullmatch(find, original, flags=re_flags)
        if check:
            await message.reply_text("Nice try 😏")
            return

        new_text = re.sub(find, replace, original, count=count, flags=re_flags)

        if new_text == original:
            await message.reply_text("No match found.")
            return

        if len(new_text) > constants.MessageLimit.MAX_TEXT_LENGTH:
            await message.reply_text("Result too long to send.")
            return

        if new_text.strip():
            sender = reply.from_user
            name = sender.first_name if sender else "Someone"
            await reply.reply_text(f"<b>{name}</b> meant:\n{new_text}", parse_mode="HTML")

    except re.error:
        await message.reply_text("Invalid regex pattern.")
    except Exception as e:
        logger.error("SED error: %s", e)


def register(app: Application):
    app.add_handler(MessageHandler(
        filters.Regex(rf"^s[{re.escape(DELIMITERS)}]") & filters.ChatType.GROUPS,
        sed,
    ))
