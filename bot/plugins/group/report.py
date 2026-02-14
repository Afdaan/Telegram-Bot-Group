import html
from telegram import Update, ChatMember
from telegram.error import BadRequest, Forbidden
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from telegram.helpers import mention_html
from bot.database.repo import Repository
from bot.logger import get_logger
from bot.utils.decorators import group_only, admin_only

logger = get_logger(__name__)

REPORT_GROUP = 5


async def report(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.effective_message or not update.effective_user:
        return
    if update.effective_chat.type not in ("group", "supergroup"):
        return

    message = update.effective_message
    chat = update.effective_chat
    user = update.effective_user

    member = await context.bot.get_chat_member(chat.id, user.id)
    if member.status in ("administrator", "creator"):
        return

    settings = await Repository.get_or_create_settings(chat.id)
    if not settings.report_enabled:
        return

    if not message.reply_to_message:
        await message.reply_text("Reply to a message to report it to admins.")
        return

    reported_user = message.reply_to_message.from_user
    if reported_user.id == user.id:
        await message.reply_text("You can't report yourself.")
        return

    if reported_user.id == context.bot.id:
        await message.reply_text("Nice try.")
        return

    reported_member = await context.bot.get_chat_member(chat.id, reported_user.id)
    if reported_member.status in ("administrator", "creator"):
        await message.reply_text("You can't report an admin.")
        return

    args = message.text.split(None, 1)
    reason = args[1] if len(args) > 1 else ""

    admins = await context.bot.get_chat_administrators(chat.id)

    admin_mentions = []
    for admin in admins:
        if admin.user.is_bot:
            continue
        admin_mentions.append(mention_html(admin.user.id, admin.user.first_name))

    report_text = (
        f"🚨 <b>Report</b>\n"
        f"<b>Reported:</b> {mention_html(reported_user.id, reported_user.first_name)}\n"
        f"<b>By:</b> {mention_html(user.id, user.first_name)}"
    )
    if reason:
        report_text += f"\n<b>Reason:</b> {html.escape(reason)}"

    if admin_mentions:
        report_text += f"\n\n👮 {' '.join(admin_mentions)}"

    await message.reply_to_message.reply_text(report_text, parse_mode="HTML")

    for admin in admins:
        if admin.user.is_bot:
            continue
        try:
            dm_text = (
                f"🚨 <b>Report in {html.escape(chat.title)}</b>\n"
                f"<b>Reported:</b> {mention_html(reported_user.id, reported_user.first_name)}\n"
                f"<b>By:</b> {mention_html(user.id, user.first_name)}"
            )
            if reason:
                dm_text += f"\n<b>Reason:</b> {html.escape(reason)}"

            if chat.username:
                dm_text += (
                    f"\n\n<a href=\"https://t.me/{chat.username}/{message.reply_to_message.message_id}\">"
                    f"Go to message</a>"
                )

            await context.bot.send_message(admin.user.id, dm_text, parse_mode="HTML")
        except (BadRequest, Forbidden):
            pass

    logger.info("REPORT %s reported %s in %s",
                user.first_name, reported_user.first_name, chat.title)


@group_only
@admin_only
async def reports_setting(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    args = update.effective_message.text.split()

    if len(args) < 2:
        settings = await Repository.get_or_create_settings(chat_id)
        status = "✅ Enabled" if settings.report_enabled else "❌ Disabled"
        await update.effective_message.reply_text(
            f"📋 Report settings:\n"
            f"  Status: {status}\n\n"
            f"Usage:\n"
            f"  /reports on - Enable reporting\n"
            f"  /reports off - Disable reporting"
        )
        return

    action = args[1].lower()
    await Repository.upsert_group(chat_id, title=update.effective_chat.title)

    if action in ("on", "yes", "enable"):
        await Repository.update_settings(chat_id, report_enabled=1)
        await update.effective_message.reply_text("📋 Reporting enabled! Use /report or @admin to report users.")
    elif action in ("off", "no", "disable"):
        await Repository.update_settings(chat_id, report_enabled=0)
        await update.effective_message.reply_text("📋 Reporting disabled.")
    else:
        await update.effective_message.reply_text("Usage: /reports <on|off>")


def register(app: Application):
    app.add_handler(CommandHandler("report", report), group=REPORT_GROUP)
    app.add_handler(CommandHandler("reports", reports_setting))
    app.add_handler(MessageHandler(
        filters.Regex(r"(?i)@admin(s)?") & filters.ChatType.GROUPS,
        report,
    ), group=REPORT_GROUP)
