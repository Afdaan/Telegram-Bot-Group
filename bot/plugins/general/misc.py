import time
from telegram import Update
from telegram.constants import ParseMode
from telegram.ext import Application, CommandHandler, ContextTypes, MessageHandler, filters

from bot.logger import get_logger

logger = get_logger(__name__)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.info("Start command received from %s", update.effective_user.id)
    user = update.effective_user
    await update.effective_message.reply_html(
        f"Hi {user.mention_html()}! \U0001f44b\n\n"
        "I am a modular group management bot.\n"
        "Use /help to see available commands."
    )

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    help_text = (
        "<b>Available Commands:</b>\n\n"
        "<b>\U0001f46e Admin Only:</b>\n"
        "/ban, /unban - Ban/Unban user\n"
        "/mute, /unmute - Mute/Unmute user\n"
        "/kick - Kick user\n"
        "/warn, /unwarn - Warn management\n"
        "/purge - Delete messages\n"
        "/pin, /unpin - Pin management\n\n"
        
        "<b>\u2699\ufe0f Group Settings:</b>\n"
        "/setup - Interactive setup\n"
        "/rules - Set/view rules\n"
        "/slowmode - Set slowmode delay\n"
        "/antiflood - Configure anti-flood\n\n"

        "<b>\U0001f3a8 Stickers:</b>\n"
        "/kang - Add sticker to your pack\n"
        "/newpack - Create new sticker pack\n"
        "/addsticker - Add sticker to named pack\n"
        "/delsticker - Remove sticker from pack\n"
        "/mypacks - List your packs\n"
        "/tophoto - Convert sticker to photo\n\n"

        "<b>\u2139\ufe0f General:</b>\n"
        "/start - Check if I'm alive\n"
        "/help - Show this message\n"
        "/ping - Check latency"
    )
    await update.effective_message.reply_text(help_text, parse_mode=ParseMode.HTML)

async def ping(update: Update, context: ContextTypes.DEFAULT_TYPE):
    start_time = time.time()
    message = await update.effective_message.reply_text("Pong!")
    end_time = time.time()
    elapsed_time = round((end_time - start_time) * 1000, 3)
    await message.edit_text(f"Pong! \U0001f3d3\nLatency: {elapsed_time}ms")

async def debug_all(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.info("Received update: %s", update.to_dict())

def register(app: Application):
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("ping", ping))
    app.add_handler(MessageHandler(filters.ALL, debug_all), group=1)
