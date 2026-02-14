from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes
from bot.database.repo import Repository
from bot.logger import get_logger
from bot.utils.decorators import group_only, admin_only, bot_admin_required, skip_old_updates
from bot.utils.parse import extract_user, check_target_not_admin

logger = get_logger(__name__)


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
    warned_by = update.effective_user.id

    if not await check_target_not_admin(update, context, user_id):
        return

    args = update.effective_message.text.split(maxsplit=2)
    reason = args[2] if len(args) > 2 else "No reason provided"

    if update.effective_message.reply_to_message and len(args) > 1:
        reason = " ".join(args[1:])

    await Repository.upsert_user(user_id, first_name=name)
    await Repository.upsert_group(chat_id, title=update.effective_chat.title)
    settings = await Repository.get_or_create_settings(chat_id)

    warning, count = await Repository.add_warning(user_id, chat_id, reason, warned_by)

    if count >= settings.warn_limit:
        await context.bot.ban_chat_member(chat_id=chat_id, user_id=user_id)
        await Repository.reset_warnings(user_id, chat_id)
        await update.effective_message.reply_text(
            f"🚫 {name} has been banned after reaching {settings.warn_limit} warnings."
        )
        logger.info("WARN-BAN %s → %s (%s) in %s [%d/%d]",
                    update.effective_user.first_name, name, user_id,
                    update.effective_chat.title, count, settings.warn_limit)
        return

    await update.effective_message.reply_text(
        f"⚠️ {name} has been warned ({count}/{settings.warn_limit}).\n"
        f"Reason: {reason}"
    )
    logger.info("WARN %s → %s (%s) in %s [%d/%d] reason: %s",
                update.effective_user.first_name, name, user_id,
                update.effective_chat.title, count, settings.warn_limit, reason)


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

    if not user_warnings:
        await update.effective_message.reply_text(f"✅ {name} has no warnings.")
        return

    lines = [f"⚠️ Warnings for {name} ({len(user_warnings)} total):"]
    for i, w in enumerate(user_warnings, 1):
        lines.append(f"  {i}. {w.reason} — {w.created_at.strftime('%Y-%m-%d %H:%M')}")

    await update.effective_message.reply_text("\n".join(lines))


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


def register(app: Application):
    app.add_handler(CommandHandler("warn", warn))
    app.add_handler(CommandHandler("warns", warns))
    app.add_handler(CommandHandler("resetwarns", resetwarns))
