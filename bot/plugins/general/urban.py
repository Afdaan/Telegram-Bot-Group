import html
import httpx
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes
from bot.logger import get_logger

logger = get_logger(__name__)

URBAN_API = "https://api.urbandictionary.com/v0/define"
USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36"

async def urban(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.effective_message.reply_text("Usage: /ud <word>")
        return

    term = " ".join(context.args)
    try:
        async with httpx.AsyncClient(headers={"User-Agent": USER_AGENT}) as client:
            response = await client.get(URBAN_API, params={"term": term}, timeout=10.0)
            if response.status_code != 200:
                logger.error(f"Urban Dictionary API returned status {response.status_code}")
                await update.effective_message.reply_text("❌ Urban Dictionary is currently unavailable.")
                return
            data = response.json()
    except Exception as e:
        logger.error(f"Error fetching from Urban Dictionary: {e}")
        await update.effective_message.reply_text("❌ Error connecting to Urban Dictionary.")
        return

    if not data.get("list"):
        await update.effective_message.reply_text(f"❌ No definition found for '<b>{html.escape(term)}</b>'.", parse_mode="HTML")
        return

    result = data["list"][0]
    
    word = result.get("word", term)
    definition = result.get("definition", "No definition.")
    example = result.get("example", "")
    permalink = result.get("permalink")

    definition = definition.replace("[", "").replace("]", "")
    if example:
        example = example.replace("[", "").replace("]", "")

    text = f"📚 <b>Urban Dictionary: {html.escape(word)}</b>\n\n"
    text += f"<b>Definition:</b>\n<i>{html.escape(definition)}</i>\n\n"
    
    if example:
        text += f"<b>Example:</b>\n<i>{html.escape(example)}</i>\n\n"
        
    text += f"🔗 <a href='{permalink}'>View on Urban Dictionary</a>"

    await update.effective_message.reply_text(text, parse_mode="HTML", disable_web_page_preview=True)


def register(app: Application):
    app.add_handler(CommandHandler("ud", urban))
