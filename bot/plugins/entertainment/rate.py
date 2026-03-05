import random
import html
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

async def rate(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.effective_message.reply_html("🔍 <b>Usage:</b> <code>/rate &lt;item&gt;</code>")
        return
        
    item = " ".join(context.args)
    percentage = random.randint(0, 100)
    
    await update.effective_message.reply_html(
        f"📊 I rate <b>{html.escape(item)}</b> at <b>{percentage}%</b>"
    )

def register(app: Application):
    app.add_handler(CommandHandler("rate", rate))
