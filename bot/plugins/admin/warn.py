import re
import html
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.error import BadRequest
from telegram.ext import (
    Application, CommandHandler, CallbackQueryHandler,
    MessageHandler, filters, ContextTypes,
)
from telegram.helpers import mention_html
from bot.database.repo import Repository
from bot.logger import get_logger
from bot.utils.decorators import group_only, admin_only, bot_admin_required, skip_old_updates
from bot.utils.parse import extract_user, check_target_not_admin
from bot.utils.string_handling import split_quotes

logger = get_logger(__name__)

WARN_FILTER_GROUP = 9


async def _do_warn(update, context, user_id, name, reason, chat_id):
    settings = await Repository.get_or_create_settings(chat_id)
    warning, count = await Repository.add_warning(user_id, chat_id, reason, update.effective_user.id)

    if count >= settings.warn_limit:
        await Repository.reset_warnings(user_id, chat_id)

        if settings.warn_action == "kick":
            await context.bot.ban_chat_member(chat_id=chat_id, user_id=user_id)
            await context.bot.unban_chat_member(chat_id=chat_id, user_id=user_id)
            action_text = "kicked"
            emoji = "👢"
        else:
            await context.bot.ban_chat_member(chat_id=chat_id, user_id=user_id)
            action_text = "banned"
            emoji = "🚫"

        await update.effective_message.reply_text(
            f"{emoji} {mention_html(user_id, name)} has been {action_text} "
            f"after reaching {settings.warn_limit} warnings!",
            parse_mode="HTML",
        )
        logger.info("WARN-%s %s → %s (%s) in %s [%d/%d]",
                     action_text.upper(), update.effective_user.first_name,
                     name, user_id, update.effective_chat.title,
                     count, settings.warn_limit)
        return

    keyboard = InlineKeyboardMarkup([[
        InlineKeyboardButton("❌ Remove Warn", callback_data=f"rm_warn:{user_id}"),
    ]])

    await update.effective_message.reply_text(
        f"⚠️ {mention_html(user_id, name)} has been warned "
        f"({count}/{settings.warn_limit}).\n"
        f"Reason: {html.escape(reason)}",
        parse_mode="HTML",
        reply_markup=keyboard,
    )
    logger.info("WARN %s → %s (%s) in %s [%d/%d] reason: %s",
                update.effective_user.first_name, name, user_id,
                update.effective_chat.title, count, settings.warn_limit, reason)


@skip_old_updates
@group_only
@admin_only
@bot_admin_required
async def warn(update: Update, context: ContextTypes.DEFAULT_TYPE):
    target = await extract_user(update)
    if not target:
        await update.effective_message.reply_text("Usage: /warn <reply|@user|id> [reason]")
        return

    user_id, name = target
    chat_id = update.effective_chat.id

    if not await check_target_not_admin(update, context, user_id):
        return

    args = update.effective_message.text.split(maxsplit=2)
    reason = args[2] if len(args) > 2 else "No reason provided"

    if update.effective_message.reply_to_message and len(args) > 1:
        reason = " ".join(args[1:])

    await Repository.upsert_user(user_id, first_name=name)
    await Repository.upsert_group(chat_id, title=update.effective_chat.title)

    await _do_warn(update, context, user_id, name, reason, chat_id)


async def remove_warn_button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user = update.effective_user
    chat = update.effective_chat

    member = await context.bot.get_chat_member(chat.id, user.id)
    if member.status not in ("administrator", "creator"):
        await query.answer("Only admins can remove warns.", show_alert=True)
        return

    match = re.match(r"rm_warn:(\d+)", query.data)
    if not match:
        return

    target_id = int(match.group(1))
    removed = await Repository.remove_last_warning(target_id, chat.id)

    if removed:
        await query.message.edit_text(
            f"✅ Warn removed by {mention_html(user.id, user.first_name)}.",
            parse_mode="HTML",
        )
        logger.info("UNWARN %s removed warn for %s in %s",
                     user.first_name, target_id, chat.title)
    else:
        await query.message.edit_text("User has no warnings.")

    await query.answer()


@group_only
async def warns(update: Update, context: ContextTypes.DEFAULT_TYPE):
    target = await extract_user(update)
    if not target:
        user_id = update.effective_user.id
        name = update.effective_user.first_name
    else:
        user_id, name = target

    chat_id = update.effective_chat.id
    user_warnings = await Repository.get_warnings(user_id, chat_id)
    settings = await Repository.get_or_create_settings(chat_id)

    if not user_warnings:
        await update.effective_message.reply_text(f"✅ {name} has no warnings.")
        return

    lines = [f"⚠️ <b>Warnings for {html.escape(name)}</b> ({len(user_warnings)}/{settings.warn_limit}):"]
    for i, w in enumerate(user_warnings, 1):
        lines.append(f"  {i}. {html.escape(w.reason)} — <i>{w.created_at.strftime('%Y-%m-%d %H:%M')}</i>")

    await update.effective_message.reply_text("\n".join(lines), parse_mode="HTML")


@skip_old_updates
@group_only
@admin_only
async def resetwarns(update: Update, context: ContextTypes.DEFAULT_TYPE):
    target = await extract_user(update)
    if not target:
        await update.effective_message.reply_text("Usage: /resetwarns <reply|@user|id>")
        return

    user_id, name = target
    chat_id = update.effective_chat.id

    deleted = await Repository.reset_warnings(user_id, chat_id)
    await update.effective_message.reply_text(f"✅ Cleared {deleted} warning(s) for {name}.")
    logger.info("RESETWARNS %s → %s (%s) in %s [cleared %d]",
                update.effective_user.first_name, name, user_id,
                update.effective_chat.title, deleted)


@group_only
@admin_only
async def warnlimit(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    args = update.effective_message.text.split()

    if len(args) < 2:
        settings = await Repository.get_or_create_settings(chat_id)
        await update.effective_message.reply_text(
            f"📋 Current warn limit: {settings.warn_limit}\n"
            f"Action on limit: {settings.warn_action}\n\n"
            f"Usage: /warnlimit <number>"
        )
        return

    if not args[1].isdigit():
        await update.effective_message.reply_text("Give me a number.")
        return

    limit = int(args[1])
    if limit < 3:
        await update.effective_message.reply_text("Minimum warn limit is 3.")
        return

    await Repository.upsert_group(chat_id, title=update.effective_chat.title)
    await Repository.update_settings(chat_id, warn_limit=limit)
    await update.effective_message.reply_text(f"✅ Warn limit set to {limit}.")
    logger.info("WARNLIMIT %s set limit to %d in %s",
                update.effective_user.first_name, limit, update.effective_chat.title)


@group_only
@admin_only
async def strongwarn(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    args = update.effective_message.text.split()

    settings = await Repository.get_or_create_settings(chat_id)

    if len(args) < 2:
        current = "🔨 Ban" if settings.warn_action == "ban" else "👢 Kick"
        await update.effective_message.reply_text(
            f"📋 Current action on warn limit: {current}\n\n"
            f"Usage:\n"
            f"  /strongwarn on — ban on limit\n"
            f"  /strongwarn off — kick on limit"
        )
        return

    action = args[1].lower()
    await Repository.upsert_group(chat_id, title=update.effective_chat.title)

    if action in ("on", "yes", "ban"):
        await Repository.update_settings(chat_id, warn_action="ban")
        await update.effective_message.reply_text("🔨 Users will be **banned** when exceeding warn limit.")
    elif action in ("off", "no", "kick"):
        await Repository.update_settings(chat_id, warn_action="kick")
        await update.effective_message.reply_text("👢 Users will be **kicked** when exceeding warn limit.")
    else:
        await update.effective_message.reply_text("Usage: /strongwarn <on|off>")


@group_only
@admin_only
async def addwarn(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    args = update.effective_message.text.split(None, 1)

    if len(args) < 2:
        await update.effective_message.reply_text(
            'Usage: /addwarn <keyword> <reason>\n'
            'Use quotes for multi-word keywords: /addwarn "bad word" reason here'
        )
        return

    extracted = split_quotes(args[1])
    if len(extracted) < 2:
        keyword = extracted[0].lower()
        reply = ""
    else:
        keyword = extracted[0].lower()
        reply = extracted[1]

    await Repository.upsert_group(chat_id, title=update.effective_chat.title)
    await Repository.add_warn_filter(chat_id, keyword, reply)

    await update.effective_message.reply_text(
        f"⚠️ Warn filter added for '<code>{html.escape(keyword)}</code>'!",
        parse_mode="HTML",
    )
    logger.info("ADDWARN %s added warn filter '%s' in %s",
                update.effective_user.first_name, keyword, update.effective_chat.title)


@group_only
@admin_only
async def rmwarn(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    args = update.effective_message.text.split(None, 1)

    if len(args) < 2:
        await update.effective_message.reply_text("Usage: /nowarn <keyword>")
        return

    keyword = args[1].strip().lower()
    removed = await Repository.remove_warn_filter(chat_id, keyword)

    if removed:
        await update.effective_message.reply_text(f"✅ Stopped warning for '{html.escape(keyword)}'.")
    else:
        await update.effective_message.reply_text("That's not an active warn filter.")


@group_only
async def warnlist(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    warn_filters = await Repository.get_warn_filters(chat_id)

    if not warn_filters:
        await update.effective_message.reply_text("No warn filters active in this group.")
        return

    lines = ["⚠️ <b>Active warn filters:</b>\n"]
    for wf in warn_filters:
        line = f" • <code>{html.escape(wf.keyword)}</code>"
        if wf.reply:
            line += f" — {html.escape(wf.reply[:50])}"
        lines.append(line)

    await update.effective_message.reply_text("\n".join(lines), parse_mode="HTML")


async def check_warn_filters(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.effective_message or not update.effective_user:
        return
    if update.effective_chat.type not in ("group", "supergroup"):
        return

    chat_id = update.effective_chat.id
    user_id = update.effective_user.id

    member = await context.bot.get_chat_member(chat_id, user_id)
    if member.status in ("administrator", "creator"):
        return

    text = update.effective_message.text or update.effective_message.caption or ""
    if not text:
        return

    warn_filters = await Repository.get_warn_filters(chat_id)
    if not warn_filters:
        return

    for wf in warn_filters:
        pattern = r"(?:^|[\s\W])" + re.escape(wf.keyword) + r"(?:$|[\s\W])"
        if re.search(pattern, text, flags=re.IGNORECASE):
            name = update.effective_user.first_name
            reason = wf.reply if wf.reply else f"Matched warn filter: {wf.keyword}"

            await Repository.upsert_user(user_id, first_name=name)
            await _do_warn(update, context, user_id, name, reason, chat_id)
            break


def register(app: Application):
    app.add_handler(CommandHandler("warn", warn))
    app.add_handler(CommandHandler("warns", warns))
    app.add_handler(CommandHandler("resetwarns", resetwarns))
    app.add_handler(CommandHandler("warnlimit", warnlimit))
    app.add_handler(CommandHandler("strongwarn", strongwarn))
    app.add_handler(CommandHandler("addwarn", addwarn))
    app.add_handler(CommandHandler(["nowarn", "stopwarn", "rmwarn"], rmwarn))
    app.add_handler(CommandHandler(["warnlist", "warnfilters"], warnlist))
    app.add_handler(CallbackQueryHandler(remove_warn_button, pattern=r"^rm_warn:"))
    app.add_handler(MessageHandler(
        (filters.TEXT | filters.CAPTION) & filters.ChatType.GROUPS & ~filters.COMMAND,
        check_warn_filters,
    ), group=WARN_FILTER_GROUP)
