import asyncio
import html

import httpx
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, ContextTypes

from bot.logger import get_logger

logger = get_logger(__name__)

async def anime_search(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.effective_message.reply_html("🔍 <b>Usage:</b> <code>/anime &lt;title&gt;</code>")
        return

    query = " ".join(context.args)
    url = f"https://api.jikan.moe/v4/anime?q={query}&limit=1"

    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(url)
            data = response.json()

        if not data.get("data"):
            await update.effective_message.reply_text(f"No anime found for '{html.escape(query)}'.")
            return

        anime = data["data"][0]
        title = anime.get("title")
        score = anime.get("score", "N/A")
        episodes = anime.get("episodes", "Unknown")
        status = anime.get("status", "Unknown")
        synopsis = anime.get("synopsis", "No synopsis available.")
        if len(synopsis) > 400:
            synopsis = synopsis[:400] + "..."

        text = (
            f"📺 <b>{html.escape(title)}</b>\n\n"
            f"⭐️ <b>Score:</b> {score}\n"
            f"🎞️ <b>Episodes:</b> {episodes}\n"
            f"📡 <b>Status:</b> {status}\n\n"
            f"📖 <b>Synopsis:</b>\n<i>{html.escape(synopsis)}</i>"
        )

        keyboard = InlineKeyboardMarkup([[
            InlineKeyboardButton("🔗 View on MAL", url=anime.get("url"))
        ]])

        await update.effective_message.reply_photo(
            photo=anime["images"]["jpg"]["large_image_url"],
            caption=text,
            reply_markup=keyboard,
            parse_mode="HTML"
        )

    except Exception as e:
        logger.error(f"Jikan API error: {e}")
        await update.effective_message.reply_text("An error occurred while fetching anime data.")

async def manga_search(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.effective_message.reply_html("🔍 <b>Usage:</b> <code>/manga &lt;title&gt;</code>")
        return

    query = " ".join(context.args)
    mal_url = f"https://api.jikan.moe/v4/manga?q={query}&limit=1"
    md_url = f"https://api.mangadex.org/manga?title={query}&limit=1"

    try:
        async with httpx.AsyncClient() as client:
            mal_res, md_res = await asyncio.gather(
                client.get(mal_url),
                client.get(md_url)
            )
            
        mal_data = mal_res.json()
        md_data = md_res.json()

        if not mal_data.get("data") and not md_data.get("data"):
            await update.effective_message.reply_text(f"No manga found for '{html.escape(query)}'.")
            return

        buttons = []
        
        if mal_data.get("data"):
            manga = mal_data["data"][0]
            title = manga.get("title")
            score = manga.get("score", "N/A")
            chapters = manga.get("chapters", "Unknown")
            status = manga.get("status", "Unknown")
            synopsis = manga.get("synopsis", "No synopsis available.")
            if synopsis and len(synopsis) > 400:
                synopsis = synopsis[:400] + "..."

            text = (
                f"📖 <b>{html.escape(str(title))}</b>\n\n"
                f"⭐️ <b>Score:</b> {score}\n"
                f"📚 <b>Chapters:</b> {chapters}\n"
                f"📡 <b>Status:</b> {status}\n\n"
                f"📝 <b>Synopsis:</b>\n<i>{html.escape(str(synopsis))}</i>"
            )
            photo_url = manga["images"]["jpg"]["large_image_url"]
            buttons.append(InlineKeyboardButton("🔗 View on MAL", url=manga.get("url")))
        else:
            md_manga = md_data["data"][0]
            attrs = md_manga["attributes"]
            title = attrs["title"].get("en") or list(attrs["title"].values())[0]
            text = f"📖 <b>{html.escape(str(title))}</b>\n\n<i>MAL info not found, but found on MangaDex.</i>"
            photo_url = None

        if md_data.get("data"):
            md_id = md_data["data"][0]["id"]
            buttons.append(InlineKeyboardButton("� View on MangaDex", url=f"https://mangadex.org/title/{md_id}"))

        keyboard = InlineKeyboardMarkup([buttons])

        if photo_url:
            await update.effective_message.reply_photo(
                photo=photo_url,
                caption=text,
                reply_markup=keyboard,
                parse_mode="HTML"
            )
        else:
            await update.effective_message.reply_text(
                text=text,
                reply_markup=keyboard,
                parse_mode="HTML"
            )

    except Exception as e:
        logger.error(f"Manga search error: {e}")
        await update.effective_message.reply_text("An error occurred while fetching manga data.")

def register(app: Application):
    app.add_handler(CommandHandler("anime", anime_search))
    app.add_handler(CommandHandler("manga", manga_search))
