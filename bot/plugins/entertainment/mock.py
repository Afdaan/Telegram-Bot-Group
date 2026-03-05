import random
import html
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

async def mock(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = update.effective_message
    
    if message.reply_to_message and (message.reply_to_message.text or message.reply_to_message.caption):
        text = message.reply_to_message.text or message.reply_to_message.caption
    elif context.args:
        text = " ".join(context.args)
    else:
        await message.reply_html("🔍 <b>Usage:</b> Reply to a message or provide text with <code>/mock</code>")
        return
        
    mocked = "".join(c.upper() if i % 2 == 0 else c.lower() for i, c in enumerate(text))
    await message.reply_html(f"<b>{html.escape(mocked)}</b>")

def register(app: Application):
    app.add_handler(CommandHandler("mock", mock))
