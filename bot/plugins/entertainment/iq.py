import random
import html
import time
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes
from bot.utils.parse import extract_user

async def iq_check(update: Update, context: ContextTypes.DEFAULT_TYPE):
    target = await extract_user(update)
    user_id = target[0] if target else update.effective_user.id
    name = target[1] if target else update.effective_user.first_name
    
    day_seed = int(time.time() / 86400)
    random.seed(user_id + day_seed)
    iq = random.randint(50, 165)
    random.seed()
    
    if iq < 70:
        comment = "Room temperature IQ. 🧊"
    elif iq < 90:
        comment = "A bit slow, but getting there. 🐢"
    elif iq < 110:
        comment = "Perfectly average. 👤"
    elif iq < 130:
        comment = "Smart cookie! 🍪"
    elif iq < 150:
        comment = "Einstein territory. 🧠"
    else:
        comment = "Actual Galaxy Brain. 🌌"
        
    text = f"🧠 <b>{html.escape(name)}'s IQ analysis:</b>\nScore: <b>{iq}</b>\n<i>{comment}</i>"
    await update.effective_message.reply_html(text)

def register(app: Application):
    app.add_handler(CommandHandler("iq", iq_check))
