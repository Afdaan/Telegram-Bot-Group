import html
import time
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, MessageEntity
from telegram.constants import ParseMode
from telegram.ext import Application, CommandHandler, ContextTypes, MessageHandler, CallbackQueryHandler, filters

from bot.logger import get_logger
from bot.utils.user_cache import remember_user
from bot.database.repo import Repository

logger = get_logger(__name__)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.info("Start command received from %s", update.effective_user.id)
    user = update.effective_user
    
    await Repository.upsert_user(
        telegram_id=user.id,
        username=user.username,
        first_name=user.first_name
    )

    if context.args:
        arg = context.args[0]
        if arg == "newpack":
            await update.effective_message.reply_html(
                f"Hey {user.mention_html()}! \U0001f3a8\n\n"
                "Let's create your first sticker pack!\n\n"
                "<b>Send a photo or reply to a sticker, then use:</b>\n"
                "<code>/newpack Your Pack Name</code>\n\n"
                "After creating your pack, you can use /kang and /addsticker in any group!"
            )
            return
        
        if arg.startswith("rules_"):
            try:
                chat_id = int(arg.split("_")[1])
                settings = await Repository.get_or_create_settings(chat_id)
                if settings and settings.rules_text:
                    group = await Repository.get_group(chat_id)
                    title = group.title if group else "the group"
                    await update.effective_message.reply_html(
                        f"📜 <b>Rules for {html.escape(title)}</b>\n\n{html.escape(settings.rules_text)}"
                    )
                    return
            except Exception as e:
                logger.error(f"Error showing rules in start: {e}")

    await update.effective_message.reply_html(
        f"Hi {user.mention_html()}! \U0001f44b\n\n"
        "I am a modular group management bot.\n"
        "Use /help to see available commands."
    )

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = (
        "👋 <b>Welcome to Alisa Help!</b>\n\n"
        "I am a powerful group management bot. Select a category below to see my commands."
    )
    
    keyboard = InlineKeyboardMarkup([
        [
            InlineKeyboardButton("🤖 Admin", callback_data="help_cat:admin"),
            InlineKeyboardButton("⚙️ Group", callback_data="help_cat:group"),
        ],
        [
            InlineKeyboardButton("✨ General", callback_data="help_cat:general"),
            InlineKeyboardButton("🎨 Sticker", callback_data="help_cat:sticker"),
        ],
        [
            InlineKeyboardButton("📡 RSS & Filters", callback_data="help_cat:rss"),
            InlineKeyboardButton("🛠️ Tools", callback_data="help_cat:tools"),
        ],
        [
            InlineKeyboardButton("🌸 Anime", callback_data="help_cat:anime"),
            InlineKeyboardButton("\U0001f3ad Entertainment", callback_data="help_cat:entertainment"),
        ],
        [
            InlineKeyboardButton("🗑️ Close Menu", callback_data="help_cat:close")
        ]
    ])
    
    if update.callback_query:
        await update.callback_query.message.edit_text(text, parse_mode=ParseMode.HTML, reply_markup=keyboard)
    else:
        await update.effective_message.reply_text(text, parse_mode=ParseMode.HTML, reply_markup=keyboard)

async def help_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    category = query.data.split(":")[1]

    if category == "close":
        await query.message.delete()
        return

    help_map = {
        "admin": (
            "👮 <b>Admin Commands:</b>\n\n"
            "/ban, /unban - Ban/Unban user\n"
            "/kick - Kick user\n"
            "/mute, /unmute - Mute/Unmute user\n"
            "/timeout - Restrict user for a duration\n"
            "/purge - Delete messages\n"
            "/pin, /unpin - Pin management\n"
            "/warn, /unwarn - Warn user\n"
            "/warns, /resetwarns - View/Reset warns\n"
            "/warnlimit - Set warn limit\n"
            "/strongwarn - Ban/Kick on limit"
        ),
        "group": (
            "⚙️ <b>Group Settings:</b>\n\n"
            "/setup - Configuration wizard\n"
            "/rules, /setrules - Rules management\n"
            "/setwelcome, /resetwelcome - Welcome msg\n"
            "/slowmode - Chat slowmode\n"
            "/antiflood, /flood - Flood protection\n"
            "/reports - Toggle reporting\n"
            "/report or @admin - Report msg"
        ),
        "general": (
            "✨ <b>General Commands:</b>\n\n"
            "/start - Start & Deep links\n"
            "/ping - Latency check\n"
            "/afk - Set AFK status\n"
            "/ud - Urban Dictionary\n"
            "/userinfo - Detailed profile"
        ),
        "sticker": (
            "🎨 <b>Sticker Commands:</b>\n\n"
            "/kang - Add to default pack\n"
            "/newpack - Create new pack\n"
            "/addsticker - Add to named pack\n"
            "/delsticker - Delete from pack\n"
            "/mypacks - List your packs\n"
            "/tophoto, /togif, /tosticker - Converts"
        ),
        "rss": (
            "📡 <b>RSS & Filters:</b>\n\n"
            "/addrss, /removerss, /listrss - RSS\n"
            "/filter, /stop, /filters - Responses\n"
            "/blacklist, /addblacklist - Blacklist"
        ),
        "tools": (
            "🛠️ <b>Tool Commands:</b>\n\n"
            "/tr - Translate text\n"
            "/wiki - Search Wikipedia\n"
            "/calc - Calculate expressions\n"
            "/qr - Generate QR Code"
        ),
        "anime": (
            "🌸 <b>Anime & Manga:</b>\n\n"
            "/sauce - Identify anime from image source\n"
            "/anime - Search anime details\n"
            "/manga - Search manga details"
        ),
        "entertainment": (
            "\U0001f3ad <b>Entertainment Commands:</b>\n\n"
            "/slap - Slap someone with an object\n"
            "/decide - Make a choice\n"
            "/pp - Check someone's pp size\n"
            "/ship - Check love compatibility\n"
            "/rate - Self-explanatory rating\n"
            "/ball8 - Ask the magic 8-ball\n"
            "/roll - Roll a dice\n"
            "/kill - Kill someone (fake)\n"
            "/iq - Check someone's IQ\n"
            "/mock - Mock some text"
        )
    }

    keyboard = InlineKeyboardMarkup([[InlineKeyboardButton("⬅️ Back", callback_data="help_cat:main")]])
    
    if category == "main":
        await help_command(update, context)
        await query.answer()
        return

    text = help_map.get(category, "Select a category.")
    await query.message.edit_text(text, parse_mode=ParseMode.HTML, reply_markup=keyboard)
    await query.answer()

async def ping(update: Update, context: ContextTypes.DEFAULT_TYPE):
    start_time = time.time()
    message = await update.effective_message.reply_text("Pong!")
    end_time = time.time()
    elapsed_time = round((end_time - start_time) * 1000, 3)
    await message.edit_text(f"Pong! \U0001f3d3\nLatency: {elapsed_time}ms")

async def debug_all(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = update.effective_message
    if not message:
        return

    async def process_user(u):
        if not u or u.is_bot:
            return
        remember_user(u)
        await Repository.upsert_user(
            telegram_id=u.id,
            username=u.username,
            first_name=u.first_name
        )

    await process_user(update.effective_user)
    await process_user(message.from_user)

    if message.reply_to_message:
        await process_user(message.reply_to_message.from_user)

    if getattr(message, "new_chat_members", None):
        for user in message.new_chat_members:
            await process_user(user)

    if getattr(message, "left_chat_member", None):
        await process_user(message.left_chat_member)

    if message.entities:
        for entity in message.entities:
            if entity.type == "text_mention" and entity.user:
                await process_user(entity.user)

def register(app: Application):
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CallbackQueryHandler(help_callback, pattern=r"^help_cat:"))
    app.add_handler(CommandHandler("ping", ping))
    app.add_handler(MessageHandler(filters.ALL, debug_all), group=1)
