from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes
from telegram.error import BadRequest, Forbidden
import httpx
from bot.database.repo import Repository
from bot.logger import get_logger
from bot.utils.decorators import group_only, admin_only, bot_admin_required, skip_old_updates

logger = get_logger(__name__)

DEFAULT_SLOWMODE = 30


async def set_slowmode(bot, chat_id: int, seconds: int):
    url = f"https://api.telegram.org/bot{bot.token}/setChatSlowModeDelay"
    async with httpx.AsyncClient() as client:
        try:
            resp = await client.post(url, json={"chat_id": chat_id, "slow_mode_delay": seconds}, timeout=10.0)
            result = resp.json()
            if not result.get("ok"):
                error_desc = result.get("description", "Unknown error")
                logger.error(f"Telegram API error: {error_desc}")
                
                if "not found" in error_desc.lower():
                    raise Exception("⚠️ Slowmode only works in supergroups. Please upgrade this group to a supergroup first.")
                elif "not enough rights" in error_desc.lower() or "forbidden" in error_desc.lower():
                    raise Exception("⚠️ Bot doesn't have permission to set slowmode. Make sure the bot is an admin with 'Change Info' permission.")
                else:
                    raise Exception(f"⚠️ {error_desc}")
            return result
        except httpx.TimeoutException:
            raise Exception("⚠️ Request timed out. Please try again.")
        except httpx.HTTPError as e:
            logger.error(f"HTTP error: {e}")
            raise Exception("⚠️ Failed to connect to Telegram API. Please try again later.")


@skip_old_updates
@group_only
@admin_only
@bot_admin_required
async def slowmode(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat = update.effective_chat
    chat_id = chat.id
    args = update.effective_message.text.split()

    if chat.type != "supergroup":
        await update.effective_message.reply_text(
            "⚠️ Slowmode only works in supergroups.\n"
            "To use this feature, you need to:\n"
            "1. Go to group settings\n"
            "2. Convert to supergroup\n"
            "3. Then try again"
        )
        return

    if len(args) < 2:
        settings = await Repository.get_or_create_settings(chat_id)
        status = "✅ Enabled" if settings.slowmode_seconds > 0 else "❌ Disabled"
        await update.effective_message.reply_text(
            f"🐢 Slowmode settings:\n"
            f"  Status: {status}\n"
            f"  Delay: {settings.slowmode_seconds} seconds\n\n"
            f"Usage:\n"
            f"  /slowmode on - Enable slowmode\n"
            f"  /slowmode off - Disable slowmode\n"
            f"  /slowmode <seconds> - Set custom delay (0-3600)"
        )
        return

    action = args[1].lower()
    await Repository.upsert_group(chat_id, title=chat.title)

    if action in ("on", "enable"):
        settings = await Repository.get_or_create_settings(chat_id)
        seconds = settings.slowmode_seconds if settings.slowmode_seconds > 0 else DEFAULT_SLOWMODE
        try:
            await set_slowmode(context.bot, chat_id, seconds)
            await Repository.update_settings(chat_id, slowmode_seconds=seconds)
            await update.effective_message.reply_text(f"🐢 Slowmode enabled: {seconds} second(s).")
            logger.info("SLOWMODE %s enabled %ds in %s",
                        update.effective_user.first_name, seconds, chat.title)
        except Exception as e:
            await update.effective_message.reply_text(f"❌ Failed to enable slowmode: {str(e)}")
            logger.error(f"Slowmode error: {e}")
        return

    if action in ("off", "disable"):
        try:
            await set_slowmode(context.bot, chat_id, 0)
            await Repository.update_settings(chat_id, slowmode_seconds=0)
            await update.effective_message.reply_text("🐢 Slowmode disabled.")
            logger.info("SLOWMODE %s disabled in %s",
                        update.effective_user.first_name, chat.title)
        except Exception as e:
            await update.effective_message.reply_text(f"❌ Failed to disable slowmode: {str(e)}")
            logger.error(f"Slowmode error: {e}")
        return

    if not action.isdigit():
        await update.effective_message.reply_text("Usage: /slowmode <on|off|seconds>")
        return

    seconds = int(action)
    if seconds < 0 or seconds > 3600:
        await update.effective_message.reply_text("Slowmode must be between 0 and 3600 seconds.")
        return

    try:
        await set_slowmode(context.bot, chat_id, seconds)
        await Repository.update_settings(chat_id, slowmode_seconds=seconds)

        if seconds == 0:
            await update.effective_message.reply_text("🐢 Slowmode disabled.")
        else:
            await update.effective_message.reply_text(f"🐢 Slowmode set to {seconds} second(s).")

        logger.info("SLOWMODE %s set to %ds in %s",
                    update.effective_user.first_name, seconds, chat.title)
    except Exception as e:
        await update.effective_message.reply_text(f"❌ Failed to set slowmode: {str(e)}")
        logger.error(f"Slowmode error: {e}")


def register(app: Application):
    app.add_handler(CommandHandler("slowmode", slowmode))
