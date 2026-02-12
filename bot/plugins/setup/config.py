from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    ConversationHandler,
    MessageHandler,
    filters,
    ContextTypes,
)
from bot.database.repo import Repository
from bot.logger import get_logger
from bot.utils.decorators import group_only, admin_only

logger = get_logger(__name__)

CHOOSING, SET_WARN_LIMIT, SET_WELCOME, SET_GOODBYE = range(4)

SETUP_KEYBOARD = InlineKeyboardMarkup([
    [
        InlineKeyboardButton("⚠️ Warn Limit", callback_data="setup_warn"),
        InlineKeyboardButton("👋 Welcome Msg", callback_data="setup_welcome"),
    ],
    [
        InlineKeyboardButton("🚪 Goodbye Msg", callback_data="setup_goodbye"),
        InlineKeyboardButton("✅ Done", callback_data="setup_done"),
    ],
])


@group_only
@admin_only
async def setup_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    await Repository.upsert_group(chat_id, title=update.effective_chat.title)
    settings = await Repository.get_or_create_settings(chat_id)

    await update.effective_message.reply_text(
        f"⚙️ Group Setup\n\n"
        f"Current settings:\n"
        f"  ⚠️ Warn limit: {settings.warn_limit}\n"
        f"  🌊 Anti-flood: {settings.antiflood_limit} msgs / {settings.antiflood_time}s\n"
        f"  🐢 Slowmode: {settings.slowmode_seconds}s\n\n"
        f"What would you like to configure?",
        reply_markup=SETUP_KEYBOARD,
    )
    return CHOOSING


async def setup_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    action = query.data

    if action == "setup_warn":
        await query.edit_message_text("Send the new warn limit (number):")
        return SET_WARN_LIMIT

    if action == "setup_welcome":
        await query.edit_message_text(
            "Send the welcome message.\n"
            "Variables: {name}, {group}\n\n"
            "Send /skip to keep current."
        )
        return SET_WELCOME

    if action == "setup_goodbye":
        await query.edit_message_text(
            "Send the goodbye message.\n"
            "Variables: {name}, {group}\n\n"
            "Send /skip to keep current."
        )
        return SET_GOODBYE

    if action == "setup_done":
        await query.edit_message_text("✅ Setup complete!")
        logger.info("SETUP complete for %s by %s",
                    update.effective_chat.title, update.effective_user.first_name)
        return ConversationHandler.END

    return CHOOSING


async def set_warn_limit(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.effective_message.text.strip()
    if not text.isdigit() or int(text) < 1:
        await update.effective_message.reply_text("Please send a valid number (minimum 1).")
        return SET_WARN_LIMIT

    chat_id = update.effective_chat.id
    await Repository.update_settings(chat_id, warn_limit=int(text))

    await update.effective_message.reply_text(
        f"✅ Warn limit set to {text}.",
        reply_markup=SETUP_KEYBOARD,
    )
    return CHOOSING


async def set_welcome_msg(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.effective_message.text.strip()
    if text == "/skip":
        await update.effective_message.reply_text("Skipped.", reply_markup=SETUP_KEYBOARD)
        return CHOOSING

    chat_id = update.effective_chat.id
    await Repository.update_settings(chat_id, welcome_msg=text)
    await update.effective_message.reply_text("✅ Welcome message updated.", reply_markup=SETUP_KEYBOARD)
    return CHOOSING


async def set_goodbye_msg(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.effective_message.text.strip()
    if text == "/skip":
        await update.effective_message.reply_text("Skipped.", reply_markup=SETUP_KEYBOARD)
        return CHOOSING

    chat_id = update.effective_chat.id
    await Repository.update_settings(chat_id, goodbye_msg=text)
    await update.effective_message.reply_text("✅ Goodbye message updated.", reply_markup=SETUP_KEYBOARD)
    return CHOOSING


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.effective_message.reply_text("Setup cancelled.")
    return ConversationHandler.END


def register(app: Application):
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("setup", setup_start)],
        states={
            CHOOSING: [CallbackQueryHandler(setup_callback, pattern=r"^setup_")],
            SET_WARN_LIMIT: [MessageHandler(filters.TEXT & ~filters.COMMAND, set_warn_limit)],
            SET_WELCOME: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, set_welcome_msg),
                CommandHandler("skip", set_welcome_msg),
            ],
            SET_GOODBYE: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, set_goodbye_msg),
                CommandHandler("skip", set_goodbye_msg),
            ],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
        per_chat=True,
        per_user=True,
    )
    app.add_handler(conv_handler)
