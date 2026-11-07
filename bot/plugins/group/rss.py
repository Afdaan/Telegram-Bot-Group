import html
import ipaddress
import re
import asyncio
import socket
from urllib.parse import urljoin, urlparse

import httpx
from feedparser import parse as feedparse
from telegram import Update
from telegram.error import BadRequest, Forbidden
from telegram.ext import Application, CommandHandler, ContextTypes
from bot.database.repo import Repository
from bot.logger import get_logger
from bot.utils.decorators import group_only, admin_only

logger = get_logger(__name__)

MAX_FEED_BYTES = 2 * 1024 * 1024
MAX_FEEDS_PER_CHAT = 20
MAX_REDIRECTS = 5
RSS_TIMEOUT = httpx.Timeout(10.0, connect=5.0)


def _entry_key(entry) -> str:
    return str(entry.get("link") or entry.get("id") or "")[:512]


async def _validate_public_url(url: str) -> None:
    parsed = urlparse(url)
    if parsed.scheme not in {"http", "https"} or not parsed.hostname:
        raise ValueError("Only public HTTP or HTTPS URLs are allowed.")
    if parsed.username or parsed.password:
        raise ValueError("URLs with embedded credentials are not allowed.")

    try:
        addresses = [ipaddress.ip_address(parsed.hostname)]
    except ValueError:
        try:
            resolved = await asyncio.to_thread(
                socket.getaddrinfo,
                parsed.hostname,
                parsed.port or (443 if parsed.scheme == "https" else 80),
                type=socket.SOCK_STREAM,
            )
        except socket.gaierror as exc:
            raise ValueError("The feed hostname could not be resolved.") from exc
        addresses = [ipaddress.ip_address(item[4][0]) for item in resolved]

    if not addresses or any(not address.is_global for address in addresses):
        raise ValueError("Private or reserved network addresses are not allowed.")


async def _fetch_feed(url: str):
    current_url = url
    async with httpx.AsyncClient(
        follow_redirects=False,
        timeout=RSS_TIMEOUT,
        trust_env=False,
        headers={"User-Agent": "AlisaTelegramBot/1.0"},
    ) as client:
        for _ in range(MAX_REDIRECTS + 1):
            await _validate_public_url(current_url)

            async with client.stream("GET", current_url) as response:
                if response.is_redirect:
                    location = response.headers.get("location")
                    if not location:
                        raise ValueError("The feed returned an invalid redirect.")
                    current_url = urljoin(current_url, location)
                    continue

                response.raise_for_status()
                body = bytearray()
                async for chunk in response.aiter_bytes():
                    body.extend(chunk)
                    if len(body) > MAX_FEED_BYTES:
                        raise ValueError("The feed is too large.")
                return feedparse(bytes(body))

    raise ValueError("The feed redirected too many times.")


async def rss_show(update: Update, context: ContextTypes.DEFAULT_TYPE):
    args = update.effective_message.text.split(None, 1)
    if len(args) < 2:
        await update.effective_message.reply_text("Usage: /rss <link>")
        return

    feed_link = args[1].strip()
    if len(feed_link) > 512:
        await update.effective_message.reply_text("❌ Feed URLs must be 512 characters or fewer.")
        return
    try:
        feed = await _fetch_feed(feed_link)
    except (ValueError, httpx.HTTPError) as exc:
        await update.effective_message.reply_text(f"❌ Unable to fetch feed: {exc}")
        return

    if feed.bozo:
        await update.effective_message.reply_text("❌ This is not a valid RSS feed link.")
        return

    title = str(feed.feed.get("title") or "Unknown")
    description = re.sub(
        r"<[^<]+?>",
        "",
        str(feed.feed.get("description") or "No description"),
    )
    link = str(feed.feed.get("link") or feed_link)[:1000]

    text = (
        f"📡 <b>{html.escape(title)}</b>\n"
        f"<i>{html.escape(description[:200])}</i>\n"
        f"🔗 {html.escape(link)}"
    )

    if feed.entries:
        entry = feed.entries[0]
        entry_title = str(entry.get("title") or "Unknown")[:512]
        entry_link = str(entry.get("link") or "")[:1000]
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
    if len(feed_link) > 512:
        await update.effective_message.reply_text("❌ Feed URLs must be 512 characters or fewer.")
        return

    feeds = await Repository.get_rss_feeds(chat_id)
    if any(item.feed_link == feed_link for item in feeds):
        await update.effective_message.reply_text("This feed has already been added.")
        return
    if len(feeds) >= MAX_FEEDS_PER_CHAT:
        await update.effective_message.reply_text(
            f"This group has reached the limit of {MAX_FEEDS_PER_CHAT} RSS feeds."
        )
        return

    try:
        feed = await _fetch_feed(feed_link)
    except (ValueError, httpx.HTTPError) as exc:
        await update.effective_message.reply_text(f"❌ Unable to fetch feed: {exc}")
        return

    if feed.bozo:
        await update.effective_message.reply_text("❌ This is not a valid RSS feed link.")
        return

    old_entry_link = ""
    if feed.entries:
        old_entry_link = _entry_key(feed.entries[0])

    added = await Repository.add_rss_feed(chat_id, feed_link, old_entry_link)

    if added:
        title = str(feed.feed.get("title") or feed_link)
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
            feed = await _fetch_feed(row.feed_link)

            if feed.bozo or not feed.entries:
                continue

            new_entries = []
            for entry in feed.entries:
                if _entry_key(entry) == row.old_entry_link:
                    break
                new_entries.append(entry)

            if not new_entries:
                continue

            to_send = list(reversed(new_entries[:5]))
            for entry in to_send:
                title = str(entry.get("title") or "No title")[:512]
                link = str(entry.get("link") or "")[:1000]
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

            await Repository.update_rss_entry(row.id, _entry_key(new_entries[0]))

        except Exception as e:
            logger.error("RSS error processing feed %s: %s", row.feed_link, e)


def register(app: Application):
    app.add_handler(CommandHandler("rss", rss_show))
    app.add_handler(CommandHandler("listrss", rss_list))
    app.add_handler(CommandHandler("addrss", rss_add))
    app.add_handler(CommandHandler("removerss", rss_remove))

    app.job_queue.run_repeating(rss_update_job, interval=120, first=30)
