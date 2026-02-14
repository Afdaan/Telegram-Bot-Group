import time
from telegram import Update
from telegram.constants import ParseMode
from telegram.ext import Application, CommandHandler, ContextTypes, MessageHandler, filters

from bot.logger import get_logger

logger = get_logger(__name__)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.info("Start command received from %s", update.effective_user.id)
    user = update.effective_user

    if context.args and context.args[0] == "newpack":
        await update.effective_message.reply_html(
            f"Hey {user.mention_html()}! \U0001f3a8\n\n"
            "Let's create your first sticker pack!\n\n"
            "<b>Send a photo or reply to a sticker, then use:</b>\n"
            "<code>/newpack Your Pack Name</code>\n\n"
            "After creating your pack, you can use /kang and /addsticker in any group!"
        )
        return

    await update.effective_message.reply_html(
        f"Hi {user.mention_html()}! \U0001f44b\n\n"
        "I am a modular group management bot.\n"
        "Use /help to see available commands."
    )

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    help_text = (
        "<b>Available Commands:</b>\n\n"

        "<b>\U0001f916 General:</b>\n"
        "/start - Check if I'm alive\n"
        "/help - Show this message\n"
        "/ping - Check bot latency\n"
        "/afk - Mark yourself as AFK\n"
        "/tr - Translate text\n"
        "/userinfo - Detailed user info\n\n"

        "<b>\U0001f46e Admin Only:</b>\n"
        "/ban, /unban - Ban/Unban user\n"
        "/kick - Kick user\n"
        "/mute, /unmute - Mute/Unmute user\n"
        "/timeout - Restrict user for a duration\n"
        "/warn, /warns, /resetwarns - Warn management\n"
        "/warnlimit - Set warn limit\n"
        "/strongwarn - Ban or kick on warn limit\n"
        "/addwarn, /nowarn, /warnlist - Warn filters\n"
        "/purge - Delete messages\n"
        "/pin, /unpin - Pin management\n\n"

        "<b>\u2699\ufe0f Group Settings:</b>\n"
        "/setup - Interactive setup wizard\n"
        "/rules, /setrules - View/set rules\n"
        "/setwelcome, /resetwelcome - Welcome message\n"
        "/slowmode - Set slowmode delay\n"
        "/antiflood, /flood - Anti-flood settings\n"
        "/reports - Enable/disable reporting\n"
        "/report - Report a message to admins\n\n"

        "<b>\U0001f516 Filters & Blacklist:</b>\n"
        "/filter, /stop, /filters - Auto-response filters\n"
        "/blacklist - View blacklisted words\n"
        "/addblacklist, /rmblacklist - Manage blacklist\n\n"

        "<b>\U0001f3a8 Stickers:</b>\n"
        "/kang - Add sticker to your pack\n"
        "/newpack - Create new sticker pack\n"
        "/addsticker - Add sticker to named pack\n"
        "/delsticker - Remove sticker from pack\n"
        "/mypacks - List your packs\n"
        "/tophoto - Convert sticker to photo\n"
        "/togif - Convert video sticker to GIF\n"
        "/tosticker - Convert GIF to video sticker\n\n"

        "<b>\U0001f4e1 RSS Feeds:</b>\n"
        "/rss - Preview an RSS feed\n"
        "/listrss - List subscriptions\n"
        "/addrss - Subscribe to a feed\n"
        "/removerss - Unsubscribe from a feed"
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
