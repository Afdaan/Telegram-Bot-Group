import random
import html
import re
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

async def decide(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.effective_message.reply_html(
            "🔍 <b>Usage:</b> <code>/decide &lt;question or choices&gt;</code>\n"
            "<b>Example:</b> <code>/decide pizza or burger</code>"
        )
        return
        
    query = " ".join(context.args)
    
    separators = [r"\s+or\s+", r"\s+atau\s+", r"\s*\|\s*", r"\s*,\s*"]
    pattern = "|".join(separators)
    
    options = [o.strip() for o in re.split(pattern, query, flags=re.IGNORECASE) if o.strip()]
    
    if len(options) >= 2:
        choice = random.choice(options)
        await update.effective_message.reply_html(f"⚖️ I've decided: <b>{html.escape(choice)}</b>")
        return

    decisions = [
        "I'd say yes.", "Definitely no.", "Go for it!", "Better not.",
        "Yes, absolutely.", "I don't think so.", "Maybe later.",
        "Seems like a good idea.", "Not worth it.", "Sure, why not?"
    ]
    await update.effective_message.reply_html(f"⚖️ My decision: <b>{random.choice(decisions)}</b>")

def register(app: Application):
    app.add_handler(CommandHandler("decide", decide))
