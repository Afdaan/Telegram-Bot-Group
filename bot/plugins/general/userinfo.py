import html
from telegram import Update, constants
from telegram.error import BadRequest
from telegram.ext import Application, CommandHandler, ContextTypes
from bot.database.repo import Repository
from bot.utils.parse import extract_user
from bot.logger import get_logger

logger = get_logger(__name__)

MAX_BIO_LENGTH = constants.MessageLimit.MAX_TEXT_LENGTH // 4


async def info(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = update.effective_message
    target = await extract_user(update)

    if target:
        user_id, _ = target
    else:
        user_id = update.effective_user.id

    try:
        chat = await context.bot.get_chat(user_id)
    except BadRequest:
        await message.reply_text("User not found.")
        return

    db_user = await Repository.get_user(user_id)

    lines = [f"👤 <b>User Info</b>\n"]
    lines.append(f"<b>ID:</b> <code>{chat.id}</code>")
    lines.append(f"<b>First Name:</b> {html.escape(chat.first_name or 'N/A')}")

    if chat.last_name:
        lines.append(f"<b>Last Name:</b> {html.escape(chat.last_name)}")

    if chat.username:
        lines.append(f"<b>Username:</b> @{html.escape(chat.username)}")

    if chat.bio:
        lines.append(f"\n<b>Telegram Bio:</b>\n<i>{html.escape(chat.bio)}</i>")

    if update.effective_chat.type in ("group", "supergroup"):
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
        except BadRequest:
            pass

        if db_user:
            warnings = await Repository.get_warnings(user_id, update.effective_chat.id)
            settings = await Repository.get_or_create_settings(update.effective_chat.id)
            lines.append(f"<b>Warnings:</b> {len(warnings)}/{settings.warn_limit}")

    if db_user:
        if db_user.about:
            lines.append(f"\n<b>About:</b>\n{html.escape(db_user.about)}")
        if db_user.bio:
            lines.append(f"\n<b>What others say:</b>\n{html.escape(db_user.bio)}")

    if db_user and db_user.created_at:
        lines.append(f"\n<b>First seen:</b> {db_user.created_at.strftime('%Y-%m-%d')}")

    try:
        photos = await context.bot.get_user_profile_photos(user_id, limit=1)
        if photos.total_count > 0:
            await message.reply_photo(
                photo=photos.photos[0][0].file_id,
                caption="\n".join(lines),
                parse_mode="HTML",
            )
            return
    except BadRequest:
        pass

    await message.reply_text("\n".join(lines), parse_mode="HTML")


async def me(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = update.effective_message
    target = await extract_user(update)

    if target:
        user_id, name = target
    else:
        user_id = update.effective_user.id
        name = update.effective_user.first_name

    db_user = await Repository.get_user(user_id)

    if db_user and db_user.about:
        await message.reply_text(
            f"<b>{html.escape(name)}</b>:\n{html.escape(db_user.about)}",
            parse_mode="HTML",
        )
    elif target:
        await message.reply_text(f"{html.escape(name)} hasn't set an about info yet.")
    else:
        await message.reply_text("You haven't set an about info yet! Use /setme <text>")


async def setme(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = update.effective_message
    user_id = update.effective_user.id
    args = message.text.split(None, 1)

    if len(args) < 2:
        await message.reply_text("Usage: /setme <text about yourself>")
        return

    text = args[1]
    if len(text) > MAX_BIO_LENGTH:
        await message.reply_text(
            f"Your info is too long! Max {MAX_BIO_LENGTH} characters, you have {len(text)}."
        )
        return

    await Repository.upsert_user(user_id,
                                  username=update.effective_user.username,
                                  first_name=update.effective_user.first_name)
    await Repository.set_user_about(user_id, text)
    await message.reply_text("✅ Updated your info!")


async def bio(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = update.effective_message
    target = await extract_user(update)

    if target:
        user_id, name = target
    else:
        user_id = update.effective_user.id
        name = update.effective_user.first_name

    db_user = await Repository.get_user(user_id)

    if db_user and db_user.bio:
        await message.reply_text(
            f"<b>{html.escape(name)}</b>:\n{html.escape(db_user.bio)}",
            parse_mode="HTML",
        )
    elif target:
        await message.reply_text(f"{html.escape(name)} doesn't have a bio set yet.")
    else:
        await message.reply_text("You don't have a bio yet! Someone else needs to set it with /setbio")


async def setbio(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = update.effective_message

    if not message.reply_to_message:
        await message.reply_text("Reply to someone's message to set their bio!")
        return

    target_user = message.reply_to_message.from_user
    setter_id = update.effective_user.id

    if target_user.id == setter_id:
        await message.reply_text("You can't set your own bio! Ask someone else to do it 😉")
        return

    if target_user.is_bot:
        await message.reply_text("You can't set a bio for bots.")
        return

    args = message.text.split(None, 1)
    if len(args) < 2:
        await message.reply_text("Usage: /setbio <text> (reply to someone)")
        return

    text = args[1]
    if len(text) > MAX_BIO_LENGTH:
        await message.reply_text(
            f"Bio is too long! Max {MAX_BIO_LENGTH} characters, you have {len(text)}."
        )
        return

    await Repository.upsert_user(target_user.id,
                                  username=target_user.username,
                                  first_name=target_user.first_name)
    await Repository.set_user_bio(target_user.id, text)
    await message.reply_text(f"✅ Updated {html.escape(target_user.first_name)}'s bio!")


def register(app: Application):
    app.add_handler(CommandHandler("userinfo", info))
    app.add_handler(CommandHandler("me", me))
    app.add_handler(CommandHandler("setme", setme))
    app.add_handler(CommandHandler("bio", bio))
    app.add_handler(CommandHandler("setbio", setbio))
