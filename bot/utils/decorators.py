from functools import wraps
from telegram import Update, ChatMember
from telegram.ext import ContextTypes


def group_only(func):
    @wraps(func)
    async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE, *args, **kwargs):
        if update.effective_chat.type not in ("group", "supergroup"):
            await update.effective_message.reply_text("⚠️ This command can only be used in groups.")
            return
        return await func(update, context, *args, **kwargs)
    return wrapper


def admin_only(func):
    @wraps(func)
    async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE, *args, **kwargs):
        chat_id = update.effective_chat.id
        user_id = update.effective_user.id
        member = await context.bot.get_chat_member(chat_id, user_id)

        if member.status not in (ChatMember.ADMINISTRATOR, ChatMember.OWNER):
            await update.effective_message.reply_text("⛔ You need admin privileges for this command.")
            return

        return await func(update, context, *args, **kwargs)
    return wrapper


def bot_admin_required(func):
    @wraps(func)
    async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE, *args, **kwargs):
        chat_id = update.effective_chat.id
        bot_member = await context.bot.get_chat_member(chat_id, context.bot.id)

        if bot_member.status not in (ChatMember.ADMINISTRATOR, ChatMember.OWNER):
            await update.effective_message.reply_text("⚠️ I need admin privileges to perform this action.")
            return

        return await func(update, context, *args, **kwargs)
    return wrapper
