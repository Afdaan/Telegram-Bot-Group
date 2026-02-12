import time
from telegram import Update
from telegram.constants import ParseMode
from telegram.ext import Application, CommandHandler, ContextTypes

from bot.logger import get_logger

logger = get_logger(__name__)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.info("Start command received from %s", update.effective_user.id)
    user = update.effective_user
    await update.message.reply_html(
        f"Hi {user.mention_html()}! 👋\n\n"
        "I am a modular group management bot.\n"
        "Use /help to see available commands."
    )

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    help_text = (
        "<b>Available Commands:</b>\n\n"
        "<b>👮 Admin Only:</b>\n"
        "/ban, /unban - Ban/Unban user\n"
        "/mute, /unmute - Mute/Unmute user\n"
        "/kick - Kick user\n"
        "/warn, /unwarn - Warn management\n"
        "/purge - Delete messages\n"
        "/pin, /unpin - Pin management\n\n"
        
        "<b>⚙️ Group Settings:</b>\n"
        "/setup - Interactive setup\n"
        "/rules - Set/view rules\n"
        "/slowmode - Set slowmode delay\n"
        "/antiflood - Configure anti-flood\n\n"

        "<b>🎨 Stickers:</b>\n"
        "/kang - Add sticker to your pack\n"
        "/pack - Create new sticker pack\n\n"

        "<b>ℹ️ General:</b>\n"
        "/start - Check if I'm alive\n"
        "/help - Show this message\n"
        "/ping - Check latency"
    )
    await update.message.reply_text(help_text, parse_mode=ParseMode.HTML)

async def ping(update: Update, context: ContextTypes.DEFAULT_TYPE):
    start_time = time.time()
    message = await update.message.reply_text("Pong!")
    end_time = time.time()
    elapsed_time = round((end_time - start_time) * 1000, 3)
    await message.edit_text(f"Pong! 🏓\nLatency: {elapsed_time}ms")

async def debug_all(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.info("Received update: %s", update.to_dict())

def register(app: Application):
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("ping", ping))
    # handler for debugging (group 1 to not interfere, but valid for inspection)
    from telegram.ext import MessageHandler, filters
    app.add_handler(MessageHandler(filters.ALL, debug_all), group=1)
