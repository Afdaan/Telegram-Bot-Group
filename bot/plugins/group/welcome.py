from telegram import Update, ChatMemberUpdated
from telegram.ext import Application, CommandHandler, ChatMemberHandler, ContextTypes
from bot.database.repo import Repository
from bot.logger import get_logger
from bot.utils.decorators import group_only, admin_only

logger = get_logger(__name__)


def _extract_status_change(chat_member_update: ChatMemberUpdated) -> tuple[bool, bool] | None:
    old = chat_member_update.old_chat_member
    new = chat_member_update.new_chat_member

    if old is None or new is None:
        return None

    was_member = old.status in ("member", "administrator", "creator")
    is_member = new.status in ("member", "administrator", "creator")

    if was_member == is_member:
        return None

    return was_member, is_member


async def on_chat_member_update(update: Update, context: ContextTypes.DEFAULT_TYPE):
    result = _extract_status_change(update.chat_member)
    if result is None:
        return

    was_member, is_member = result
    chat_id = update.effective_chat.id
    user = update.chat_member.new_chat_member.user

    await Repository.upsert_group(chat_id, title=update.effective_chat.title)
    settings = await Repository.get_or_create_settings(chat_id)

    if not was_member and is_member:
        welcome = settings.welcome_msg or f"Welcome to the group, {user.first_name}! 👋"
        welcome = welcome.replace("{name}", user.first_name or "")
        welcome = welcome.replace("{group}", update.effective_chat.title or "")
        await context.bot.send_message(chat_id=chat_id, text=welcome)

    elif was_member and not is_member:
        goodbye = settings.goodbye_msg or f"Goodbye, {user.first_name}. 👋"
        goodbye = goodbye.replace("{name}", user.first_name or "")
        goodbye = goodbye.replace("{group}", update.effective_chat.title or "")
        await context.bot.send_message(chat_id=chat_id, text=goodbye)


@group_only
@admin_only
async def setwelcome(update: Update, context: ContextTypes.DEFAULT_TYPE):
    args = update.effective_message.text.split(maxsplit=1)
    if len(args) < 2:
        await update.effective_message.reply_text(
            "Usage: /setwelcome <message>\n"
            "Variables: {name}, {group}"
        )
        return

    chat_id = update.effective_chat.id
    await Repository.upsert_group(chat_id, title=update.effective_chat.title)
    await Repository.update_settings(chat_id, welcome_msg=args[1])
    await update.effective_message.reply_text("✅ Welcome message updated.")
    logger.info("SET_WELCOME %s in %s", update.effective_user.first_name, update.effective_chat.title)


@group_only
@admin_only
async def resetwelcome(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    await Repository.update_settings(chat_id, welcome_msg=None, goodbye_msg=None)
    await update.effective_message.reply_text("✅ Welcome/goodbye messages reset to default.")
    logger.info("RESET_WELCOME %s in %s", update.effective_user.first_name, update.effective_chat.title)


def register(app: Application):
    app.add_handler(ChatMemberHandler(on_chat_member_update, ChatMemberHandler.CHAT_MEMBER))
    app.add_handler(CommandHandler("setwelcome", setwelcome))
    app.add_handler(CommandHandler("resetwelcome", resetwelcome))
