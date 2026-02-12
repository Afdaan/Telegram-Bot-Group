from telegram import ChatMember, Update
from telegram.ext import ContextTypes


async def is_admin(chat_id: int, user_id: int, context: ContextTypes.DEFAULT_TYPE) -> bool:
    member = await context.bot.get_chat_member(chat_id, user_id)
    return member.status in (ChatMember.ADMINISTRATOR, ChatMember.OWNER)


async def is_owner(chat_id: int, user_id: int, context: ContextTypes.DEFAULT_TYPE) -> bool:
    member = await context.bot.get_chat_member(chat_id, user_id)
    return member.status == ChatMember.OWNER


async def can_restrict(chat_id: int, context: ContextTypes.DEFAULT_TYPE) -> bool:
    bot_member = await context.bot.get_chat_member(chat_id, context.bot.id)
    return bot_member.status == ChatMember.ADMINISTRATOR and bot_member.can_restrict_members


async def can_delete(chat_id: int, context: ContextTypes.DEFAULT_TYPE) -> bool:
    bot_member = await context.bot.get_chat_member(chat_id, context.bot.id)
    return bot_member.status == ChatMember.ADMINISTRATOR and bot_member.can_delete_messages


async def can_pin(chat_id: int, context: ContextTypes.DEFAULT_TYPE) -> bool:
    bot_member = await context.bot.get_chat_member(chat_id, context.bot.id)
    return bot_member.status == ChatMember.ADMINISTRATOR and bot_member.can_pin_messages
