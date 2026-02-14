import html
from telegram import Update
from telegram.error import BadRequest
from telegram.ext import Application, CommandHandler, ContextTypes
from bot.database.repo import Repository
from bot.utils.parse import extract_user
from bot.logger import get_logger

logger = get_logger(__name__)


async def info(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = update.effective_message
    args = message.text.split()

    if len(args) >= 2 or message.reply_to_message:
        target = await extract_user(update)
        if target:
            user_id, _ = target
        else:
            await message.reply_text("❌ User not found. Try replying to their message or use @username or user ID.")
            return
    else:
        user_id = update.effective_user.id

    if not user_id or user_id <= 0:
        await message.reply_text("❌ Invalid user ID.")
        return

    try:
        chat = await context.bot.get_chat(user_id)
    except (BadRequest, Exception) as e:
        logger.error(f"Failed to get user info for {user_id}: {e}")
        await message.reply_text("❌ User not found or cannot retrieve user information.")
        return

    lines = await _build_user_info_lines(update, context, chat, user_id)
    await _send_user_info_response(message, user_id, lines)


async def _build_user_info_lines(update, context, chat, user_id):
    lines = [f"👤 <b>User Info</b>\n"]
    lines.append(f"<b>ID:</b> <code>{chat.id}</code>")
    lines.append(f"<b>First Name:</b> {html.escape(chat.first_name or 'N/A')}")

    if chat.last_name:
        lines.append(f"<b>Last Name:</b> {html.escape(chat.last_name)}")

    if chat.username:
        lines.append(f"<b>Username:</b> @{html.escape(chat.username)}")

    if hasattr(chat, 'bio') and chat.bio:
        lines.append(f"\n<b>Bio:</b>\n<i>{html.escape(chat.bio)}</i>")

    if update.effective_chat.type in ("group", "supergroup"):
        await _add_group_info(lines, update, context, user_id)

    return lines


async def _add_group_info(lines, update, context, user_id):
    try:
        member = await context.bot.get_chat_member(update.effective_chat.id, user_id)
        status_map = {
            "creator": "👑 Owner",
            "administrator": "⭐ Admin",
            "member": "👤 Member",
            "restricted": "🔇 Restricted",
            "left": "🚪 Left",
            "kicked": "🚫 Banned",
        }
        status = status_map.get(member.status, member.status)
        lines.append(f"\n<b>Status:</b> {status}")

        if hasattr(member, "custom_title") and member.custom_title:
            lines.append(f"<b>Title:</b> {html.escape(member.custom_title)}")
    except (BadRequest, Exception) as e:
        logger.warning(f"Failed to get chat member info for {user_id} in {update.effective_chat.id}: {e}")

    try:
        warnings = await Repository.get_warnings(user_id, update.effective_chat.id)
        settings = await Repository.get_or_create_settings(update.effective_chat.id)
        lines.append(f"<b>Warnings:</b> {len(warnings)}/{settings.warn_limit}")
    except Exception as e:
        logger.warning(f"Failed to get warnings: {e}")


async def _send_user_info_response(message, user_id, lines):
    reply_params = _prepare_reply_params(message)
    
    try:
        photos = await message.get_bot().get_user_profile_photos(user_id, limit=1)
        if photos.total_count > 0:
            reply_params["photo"] = photos.photos[0][0].file_id
            reply_params["caption"] = "\n".join(lines)
            await message.reply_photo(**reply_params)
            return
    except BadRequest as e:
        logger.debug(f"Failed to get profile photo: {e}")
    except Exception as e:
        logger.error(f"Unexpected error getting profile photo: {e}")

    reply_params["text"] = "\n".join(lines)
    await message.reply_text(**reply_params)


def _prepare_reply_params(message):
    params = {"parse_mode": "HTML"}
    if hasattr(message, 'message_thread_id') and message.message_thread_id:
        params["message_thread_id"] = message.message_thread_id
    return params



def register(app: Application):
    app.add_handler(CommandHandler("userinfo", info))
