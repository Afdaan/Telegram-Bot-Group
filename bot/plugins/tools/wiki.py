import html
import httpx
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, ContextTypes
from bot.logger import get_logger

logger = get_logger(__name__)

async def wiki(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.effective_message.reply_text("Usage: /wiki <query>")
        return

    query = " ".join(context.args)
    url = "https://en.wikipedia.org/w/api.php"
    params = {
        "action": "query",
        "format": "json",
        "prop": "extracts|info",
        "exchars": 400,
        "explaintext": True,
        "inprop": "url",
        "titles": query,
        "redirects": 1
    }

    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(url, params=params)
            data = response.json()
            
            pages = data.get("query", {}).get("pages", {})
            page_id = next(iter(pages))
            page = pages[page_id]

            if "missing" in page:
                await update.effective_message.reply_text(f"No Wikipedia article found for '{html.escape(query)}'.")
                return

            title = page.get("title")
            extract = page.get("extract", "No description available.")
            full_url = page.get("fullurl")

            text = f"📚 <b>{html.escape(title)}</b>\n\n{html.escape(extract)}"
            
            keyboard = InlineKeyboardMarkup([[
                InlineKeyboardButton("🔗 Read on Wikipedia", url=full_url)
            ]])

            await update.effective_message.reply_html(text, reply_markup=keyboard)

    except Exception as e:
        logger.error(f"Wikipedia API error: {e}")
        await update.effective_message.reply_text("An error occurred while fetching data from Wikipedia.")

def register(app: Application):
    app.add_handler(CommandHandler("wiki", wiki))
