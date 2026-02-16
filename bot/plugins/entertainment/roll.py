import random
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

async def roll(update: Update, context: ContextTypes.DEFAULT_TYPE):
    args = context.args
    min_val = 1
    max_val = 6
    
    if args:
        try:
            if "-" in args[0]:
                parts = args[0].split("-")
                min_val = int(parts[0])
                max_val = int(parts[1])
            else:
                max_val = int(args[0])
        except (ValueError, IndexError):
            await update.effective_message.reply_text("Usage: /roll [max] or /roll [min-max]")
            return

    if min_val >= max_val:
        await update.effective_message.reply_text("Max must be greater than min.")
        return

    result = random.randint(min_val, max_val)
    await update.effective_message.reply_html(f"🎲 You rolled a <b>{result}</b>!")

def register(app: Application):
    app.add_handler(CommandHandler(["roll", "rolls"], roll))
