import random
import html
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes
from bot.utils.parse import extract_user

async def pp_size(update: Update, context: ContextTypes.DEFAULT_TYPE):
    target = await extract_user(update)
    user_id = target[0] if target else update.effective_user.id
    name = target[1] if target else update.effective_user.first_name
    
    random.seed(user_id + random.getrandbits(8))
    size = random.randint(0, 30)
    random.seed()
    
    shaft = "=" * (size // 2)
    text = f"<b>{html.escape(name)}'s pp size:</b>\n8{shaft}D ({size}cm)"
    
    await update.effective_message.reply_html(text)

def register(app: Application):
    app.add_handler(CommandHandler(["pp", "size"], pp_size))
