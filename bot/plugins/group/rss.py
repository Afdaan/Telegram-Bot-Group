import html
import re
import asyncio
from functools import partial
from feedparser import parse as feedparse
from telegram import Update
from telegram.error import BadRequest, Forbidden
from telegram.ext import Application, CommandHandler, ContextTypes
from bot.database.repo import Repository
from bot.logger import get_logger
from bot.utils.decorators import group_only, admin_only

logger = get_logger(__name__)


def _parse_feed(url: str):
    return feedparse(url)


async def parse_feed_async(url: str):
    loop = asyncio.get_running_loop()
    return await loop.run_in_executor(None, partial(_parse_feed, url))


async def rss_show(update: Update, context: ContextTypes.DEFAULT_TYPE):
    args = update.effective_message.text.split(None, 1)
    if len(args) < 2:
        await update.effective_message.reply_text("Usage: /rss <link>")
        return

    feed_link = args[1].strip()
    feed = await parse_feed_async(feed_link)

    if feed.bozo:
        await update.effective_message.reply_text("❌ This is not a valid RSS feed link.")
        return

    title = feed.feed.get("title", "Unknown")
    description = re.sub(r"<[^<]+?>", "", feed.feed.get("description", "No description"))
    link = feed.feed.get("link", feed_link)

    text = (
        f"📡 <b>{html.escape(title)}</b>\n"
        f"<i>{html.escape(description[:200])}</i>\n"
        f"🔗 {html.escape(link)}"
    )

    if feed.entries:
        entry = feed.entries[0]
        entry_title = entry.get("title", "Unknown")
        entry_link = entry.get("link", "")
        text += (
            f"\n\n📰 <b>Latest:</b>\n"
            f"{html.escape(entry_title)}\n"
            f"{html.escape(entry_link)}"
        )

    await update.effective_message.reply_text(text, parse_mode="HTML")


@group_only
async def rss_list(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    feeds = await Repository.get_rss_feeds(chat_id)

    if not feeds:
        await update.effective_message.reply_text("📡 No RSS subscriptions in this group.")
        return

    lines = ["📡 <b>RSS Subscriptions:</b>\n"]
    for i, feed in enumerate(feeds, 1):
        lines.append(f"{i}. <code>{html.escape(feed.feed_link)}</code>")

    await update.effective_message.reply_text("\n".join(lines), parse_mode="HTML")


@group_only
@admin_only
async def rss_add(update: Update, context: ContextTypes.DEFAULT_TYPE):
    args = update.effective_message.text.split(None, 1)
    if len(args) < 2:
        await update.effective_message.reply_text("Usage: /addrss <link>")
        return

    chat_id = update.effective_chat.id
    feed_link = args[1].strip()

    feed = await parse_feed_async(feed_link)

    if feed.bozo:
        await update.effective_message.reply_text("❌ This is not a valid RSS feed link.")
        return

    old_entry_link = ""
    if feed.entries:
        old_entry_link = feed.entries[0].get("link", "")

    added = await Repository.add_rss_feed(chat_id, feed_link, old_entry_link)

    if added:
        title = feed.feed.get("title", feed_link)
        await update.effective_message.reply_text(
            f"✅ Subscribed to <b>{html.escape(title)}</b>",
            parse_mode="HTML",
        )
        logger.info("RSS %s added feed %s in %s",
                     update.effective_user.first_name, feed_link,
                     update.effective_chat.title)
    else:
        await update.effective_message.reply_text("This feed has already been added.")


@group_only
@admin_only
async def rss_remove(update: Update, context: ContextTypes.DEFAULT_TYPE):
    args = update.effective_message.text.split(None, 1)
    if len(args) < 2:
        await update.effective_message.reply_text("Usage: /removerss <link>")
        return

    chat_id = update.effective_chat.id
    feed_link = args[1].strip()

    removed = await Repository.remove_rss_feed(chat_id, feed_link)

    if removed:
        await update.effective_message.reply_text("✅ Unsubscribed from feed.")
        logger.info("RSS %s removed feed %s in %s",
                     update.effective_user.first_name, feed_link,
                     update.effective_chat.title)
    else:
        await update.effective_message.reply_text("This feed isn't in your subscriptions.")


async def rss_update_job(context: ContextTypes.DEFAULT_TYPE):
    feeds = await Repository.get_all_rss_feeds()

    for row in feeds:
        try:
            feed = await parse_feed_async(row.feed_link)

            if feed.bozo or not feed.entries:
                continue

            new_entries = []
            for entry in feed.entries:
                if entry.get("link") == row.old_entry_link:
                    break
                new_entries.append(entry)

            if not new_entries:
                continue

            await Repository.update_rss_entry(row.id, new_entries[0].get("link", ""))

            to_send = list(reversed(new_entries[:5]))
            for entry in to_send:
                title = entry.get("title", "No title")
                link = entry.get("link", "")
                text = f"📰 <b>{html.escape(title)}</b>\n{html.escape(link)}"

                try:
                    await context.bot.send_message(
                        chat_id=row.chat_id, text=text, parse_mode="HTML",
                    )
                except (BadRequest, Forbidden):
                    await Repository.remove_rss_feed(row.chat_id, row.feed_link)
                    logger.warning("RSS removed feed %s, bot kicked or no access", row.feed_link)
                    break

            if len(new_entries) > 5:
                try:
                    await context.bot.send_message(
                        chat_id=row.chat_id,
                        text=f"📡 <i>{len(new_entries) - 5} more entries were skipped to prevent spam.</i>",
                        parse_mode="HTML",
                    )
                except (BadRequest, Forbidden):
                    pass

        except Exception as e:
            logger.error("RSS error processing feed %s: %s", row.feed_link, e)


def register(app: Application):
    app.add_handler(CommandHandler("rss", rss_show))
    app.add_handler(CommandHandler("listrss", rss_list))
    app.add_handler(CommandHandler("addrss", rss_add))
    app.add_handler(CommandHandler("removerss", rss_remove))

    app.job_queue.run_repeating(rss_update_job, interval=120, first=30)
