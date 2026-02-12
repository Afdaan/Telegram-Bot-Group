from telegram import Update
from telegram.ext import ContextTypes
from bot.logger import get_logger

logger = get_logger(__name__)


async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE):
    logger.error("Unhandled exception: %s", context.error, exc_info=context.error)

    if isinstance(update, Update) and update.effective_message:
        await update.effective_message.reply_text(
            "❌ An unexpected error occurred. Please try again later."
        )
