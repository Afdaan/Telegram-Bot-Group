from telegram import Update
from telegram.ext import ContextTypes
from bot.logger import get_logger

logger = get_logger(__name__)


async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE):
    logger.error("Unhandled exception: %s", context.error, exc_info=context.error)

    if not isinstance(update, Update) or not update.effective_message:
        return

    message = update.effective_message
    chat = update.effective_chat
    
    is_private = chat.type == "private" if chat else False
    is_callback = bool(update.callback_query)
    
    text_content = message.text or message.caption or ""
    is_command = text_content.startswith("/")

    if is_private or is_callback or is_command:
        try:
            await message.reply_text(
                "❌ An unexpected error occurred. Please try again later."
            )
        except Exception:
            pass
