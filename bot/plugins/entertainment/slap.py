import random
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes
from telegram.helpers import mention_html
from bot.utils.parse import extract_user

async def slap(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    target = await extract_user(update)
    
    slap_items = [
        "a large trout",
        "a wet noodle",
        "a heavy dictionary",
        "a slice of pizza",
        "a rubber duck",
        "a keyboard",
        "a frying pan",
        "a cactus",
        "a collection of old floppy disks"
    ]
    
    item = random.choice(slap_items)
    
    if target:
        target_id, target_name = target
        text = f"{mention_html(user.id, user.first_name)} slaps {mention_html(target_id, target_name)} around a bit with {item}."
    else:
        text = f"{mention_html(user.id, user.first_name)} slaps themselves with {item} out of confusion."
        
    await update.effective_message.reply_html(text)

def register(app: Application):
    app.add_handler(CommandHandler("slap", slap))
