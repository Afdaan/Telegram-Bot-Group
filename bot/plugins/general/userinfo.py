import html
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ChatPermissions
from telegram.error import BadRequest
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes
from bot.database.repo import Repository
from bot.utils.parse import extract_user
from bot.logger import get_logger

logger = get_logger(__name__)


async def info(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = update.effective_message
    
    command_text = message.text or ""
    command_parts = command_text.split(None, 1)
    has_args = len(command_parts) > 1

    reply_msg = message.reply_to_message
    has_real_reply = bool(reply_msg) and not (
        reply_msg.forum_topic_created
        or reply_msg.forum_topic_edited
        or reply_msg.forum_topic_closed
        or (reply_msg.from_user and reply_msg.from_user.id == 0)
    )

    if has_args or has_real_reply:
        target = await extract_user(update)
        if target:
            user_id, username = target
        else:
            await message.reply_html(
                "🔍 <b>Usage:</b>\n"
                "  • Reply to a message with <code>/userinfo</code>\n"
                "  • <code>/userinfo &lt;@username|id&gt;</code>"
            )
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
    await _send_user_info_response(update, context, user_id, lines)


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
        error_msg = str(e)
        if "Unknown column" not in error_msg and "OperationalError" not in error_msg:
            logger.warning(f"Failed to get warnings: {e}")


async def _send_user_info_response(update, context, user_id, lines):
    message = update.effective_message
    reply_markup = None

    if update.effective_chat.type in ("group", "supergroup"):
        try:
            admin_check = await context.bot.get_chat_member(update.effective_chat.id, update.effective_user.id)
            if admin_check.status in ("administrator", "creator"):
                buttons = [
                    [
                        InlineKeyboardButton("🚫 Ban", callback_data=f"user_admin:ban:{user_id}"),
                        InlineKeyboardButton("🔇 Mute", callback_data=f"user_admin:mute:{user_id}"),
                    ],
                    [
                        InlineKeyboardButton("⚠️ Reset Warns", callback_data=f"user_admin:reset:{user_id}"),
                        InlineKeyboardButton("🗑️ Close", callback_data="user_admin:close")
                    ]
                ]
                reply_markup = InlineKeyboardMarkup(buttons)
        except Exception:
            pass

    reply_params = _prepare_reply_params(message)
    if reply_markup:
        reply_params["reply_markup"] = reply_markup
    
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


async def user_info_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    data = query.data.split(":")
    if len(data) < 2 or data[1] not in {"ban", "mute", "reset", "close"}:
        await query.answer("Invalid or expired action.", show_alert=True)
        return

    action = data[1]
    chat_id = query.message.chat.id

    try:
        member = await context.bot.get_chat_member(chat_id, query.from_user.id)
        required_right = "can_restrict_members" if action in {"ban", "mute"} else None
        allowed = member.status == "creator" or (
            member.status == "administrator"
            and (required_right is None or bool(getattr(member, required_right, False)))
        )
        if not allowed:
            await query.answer("Admin only!", show_alert=True)
            return
    except Exception as exc:
        logger.warning("Failed to authorize user info callback: %s", exc)
        await query.answer("Unable to verify your permissions.", show_alert=True)
        return

    if action == "close":
        await query.answer()
        await query.message.delete()
        return

    if len(data) != 3:
        await query.answer("Invalid or expired action.", show_alert=True)
        return

    try:
        target_id = int(data[2])
    except ValueError:
        await query.answer("Invalid or expired action.", show_alert=True)
        return

    try:
        if action in {"ban", "mute"}:
            bot_member = await context.bot.get_chat_member(chat_id, context.bot.id)
            bot_allowed = bot_member.status == "creator" or (
                bot_member.status == "administrator"
                and bool(getattr(bot_member, "can_restrict_members", False))
            )
            if not bot_allowed:
                await query.answer("The bot cannot restrict members.", show_alert=True)
                return

            target = await context.bot.get_chat_member(chat_id, target_id)
            if target.status in ("administrator", "creator"):
                await query.answer("Admins cannot be moderated.", show_alert=True)
                return

        if action == "ban":
            await context.bot.ban_chat_member(chat_id, target_id)
            result = "Banned."
        elif action == "mute":
            await context.bot.restrict_chat_member(chat_id, target_id, ChatPermissions(can_send_messages=False))
            result = "Muted."
        else:
            await Repository.reset_warnings(target_id, chat_id)
            result = "Warnings reset."

        await query.message.edit_reply_markup(None)
        await query.answer(result)
    except Exception as e:
        logger.error("User info callback failed for action %s: %s", action, e)
        await query.answer("The action failed. Check permissions and try again.", show_alert=True)


def _prepare_reply_params(message):
    params = {"parse_mode": "HTML"}
    if hasattr(message, 'message_thread_id') and message.message_thread_id:
        params["message_thread_id"] = message.message_thread_id
    return params





def register(app: Application):
    app.add_handler(CommandHandler("userinfo", info))
    app.add_handler(CallbackQueryHandler(user_info_callback, pattern=r"^user_admin:"))
