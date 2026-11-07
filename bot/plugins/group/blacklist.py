import html
import re
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.error import BadRequest
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, filters, ContextTypes
from bot.database.repo import Repository
from bot.logger import get_logger
from bot.utils.decorators import group_only, admin_only

logger = get_logger(__name__)

BLACKLIST_GROUP = 11


@group_only
async def blacklist(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    entries = await Repository.get_blacklist_entries(chat_id)

    if not entries:
        await update.effective_message.reply_text("📝 No blacklisted words in this group.")
        return

    text = (
        f"🚫 <b>Blacklisted Words in {html.escape(update.effective_chat.title or 'this group')}</b>\n\n"
        "Click a button to remove it from the list:"
    )
    
    buttons = []
    for entry in sorted(entries, key=lambda item: item.trigger):
        buttons.append([
            InlineKeyboardButton(f"🗑️ {entry.trigger}", callback_data=f"rm_bl:{entry.id}")
        ])
    
    reply_markup = InlineKeyboardMarkup(buttons)
    await update.effective_message.reply_text(text, parse_mode="HTML", reply_markup=reply_markup)


async def blacklist_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    chat_id = update.effective_chat.id

    try:
        blacklist_id = int(query.data.split(":", 1)[1])
    except (IndexError, ValueError):
        await query.answer("Invalid blacklist action.", show_alert=True)
        return
    
    member = await context.bot.get_chat_member(chat_id, update.effective_user.id)
    if member.status not in ("administrator", "creator"):
        await query.answer("Admin only!", show_alert=True)
        return

    deleted = await Repository.remove_blacklist_by_id(chat_id, blacklist_id)
    if deleted:
        await query.answer("Blacklist entry removed.")
        await blacklist(update, context)
        try:
             await query.message.delete()
        except BadRequest:
            pass
    else:
        await query.answer("Not found.")


@group_only
@admin_only
async def add_blacklist(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    args = update.effective_message.text.split(None, 1)

    if len(args) < 2:
        await update.effective_message.reply_html(
            "🔍 <b>Usage:</b> <code>/addblacklist &lt;word or phrases&gt;</code>\n"
            "Multiple words can be added on separate lines."
        )
        return

    text = args[1]
    triggers = list(set(t.strip().lower() for t in text.split("\n") if t.strip()))

    if any(len(trigger) > 255 for trigger in triggers):
        await update.effective_message.reply_text(
            "Blacklist entries must be 255 characters or fewer."
        )
        return

    await Repository.upsert_group(chat_id, title=update.effective_chat.title)

    for trigger in triggers:
        await Repository.add_blacklist(chat_id, trigger)

    if len(triggers) == 1:
        await update.effective_message.reply_text(
            f"🚫 Added <code>{html.escape(triggers[0])}</code> to the blacklist.",
            parse_mode="HTML",
        )
    else:
        await update.effective_message.reply_text(
            f"🚫 Added {len(triggers)} words to the blacklist.",
        )

    logger.info("BLACKLIST %s added %d triggers in %s",
                update.effective_user.first_name, len(triggers),
                update.effective_chat.title)


@group_only
@admin_only
async def remove_blacklist(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    args = update.effective_message.text.split(None, 1)

    if len(args) < 2:
        await update.effective_message.reply_html(
            "🔍 <b>Usage:</b> <code>/rmblacklist &lt;word or phrases&gt;</code>\n"
            "Multiple words can be removed on separate lines."
        )
        return

    text = args[1]
    triggers = list(set(t.strip().lower() for t in text.split("\n") if t.strip()))
    removed = 0

    for trigger in triggers:
        if await Repository.remove_blacklist(chat_id, trigger):
            removed += 1

    if len(triggers) == 1:
        if removed:
            await update.effective_message.reply_text(
                f"✅ Removed <code>{html.escape(triggers[0])}</code> from the blacklist.",
                parse_mode="HTML",
            )
        else:
            await update.effective_message.reply_text("This word isn't blacklisted.")
    elif removed == 0:
        await update.effective_message.reply_text("None of those words were blacklisted.")
    else:
        await update.effective_message.reply_text(
            f"✅ Removed {removed}/{len(triggers)} words from the blacklist.",
        )

    logger.info("BLACKLIST %s removed %d triggers in %s",
                update.effective_user.first_name, removed,
                update.effective_chat.title)


async def check_blacklist(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.effective_message or not update.effective_user:
        return
    if update.effective_chat.type not in ("group", "supergroup"):
        return

    chat_id = update.effective_chat.id
    user_id = update.effective_user.id

    member = await context.bot.get_chat_member(chat_id, user_id)
    if member.status in ("administrator", "creator"):
        return

    message_text = update.effective_message.text or update.effective_message.caption or ""
    if not message_text:
        return

    triggers = await Repository.get_blacklist(chat_id)
    if not triggers:
        return

    for trigger in triggers:
        pattern = r"(?:^|[\s\W])" + re.escape(trigger) + r"(?:$|[\s\W])"
        if re.search(pattern, message_text, flags=re.IGNORECASE):
            try:
                await update.effective_message.delete()
                logger.info("BLACKLIST deleted message from %s in %s (trigger: %s)",
                            update.effective_user.first_name,
                            update.effective_chat.title, trigger)
            except BadRequest:
                pass
            break


def register(app: Application):
    app.add_handler(CommandHandler("blacklist", blacklist))
    app.add_handler(CommandHandler("addblacklist", add_blacklist))
    app.add_handler(CommandHandler(["rmblacklist", "unblacklist"], remove_blacklist))
    app.add_handler(CallbackQueryHandler(blacklist_callback, pattern=r"^rm_bl:"))
    app.add_handler(MessageHandler(
        (filters.TEXT | filters.CAPTION) & filters.ChatType.GROUPS & ~filters.COMMAND,
        check_blacklist,
    ), group=BLACKLIST_GROUP)
