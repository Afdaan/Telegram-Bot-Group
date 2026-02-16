import html
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, ContextTypes
from bot.database.repo import Repository
from bot.logger import get_logger
from bot.utils.decorators import group_only, admin_only

logger = get_logger(__name__)


@group_only
async def rules(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    settings = await Repository.get_or_create_settings(chat_id)

    if not settings.rules_text:
        await update.effective_message.reply_text("📜 No rules have been set for this group.")
        return

    text = f"📜 <b>Rules for {html.escape(update.effective_chat.title)}</b>\n\n{html.escape(settings.rules_text)}"
    
    keyboard = InlineKeyboardMarkup([[
        InlineKeyboardButton("🚀 Read in Private", url=f"https://t.me/{context.bot.username}?start=rules_{chat_id}")
    ]])

    await update.effective_message.reply_text(
        text, 
        parse_mode="HTML",
        reply_markup=keyboard
    )


@group_only
@admin_only
async def setrules(update: Update, context: ContextTypes.DEFAULT_TYPE):
    args = update.effective_message.text.split(maxsplit=1)
    if len(args) < 2:
        await update.effective_message.reply_text("Usage: /setrules <rules text>")
        return

    chat_id = update.effective_chat.id
    await Repository.upsert_group(chat_id, title=update.effective_chat.title)
    await Repository.update_settings(chat_id, rules_text=args[1])
    await update.effective_message.reply_text("✅ Group rules updated.")
    logger.info("SET_RULES %s in %s", update.effective_user.first_name, update.effective_chat.title)


def register(app: Application):
    app.add_handler(CommandHandler("rules", rules))
    app.add_handler(CommandHandler("setrules", setrules))
