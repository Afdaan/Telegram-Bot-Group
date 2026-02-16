import random
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes
from telegram.helpers import mention_html

async def ship(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = update.effective_message
    user = update.effective_user
    
    if not message.reply_to_message:
        await message.reply_text("Reply to someone's message to ship them with you!")
        return
        
    target = message.reply_to_message.from_user
    if target.id == user.id:
        await message.reply_text("You can't ship yourself with yourself!")
        return
        
    percentage = random.randint(0, 100)
    
    if percentage < 25:
        comment = "Awful match. 💔"
    elif percentage < 50:
        comment = "Could work with effort. ✨"
    elif percentage < 75:
        comment = "A solid couple! ❤️"
    elif percentage < 90:
        comment = "Made for each other! 😍"
    else:
        comment = "Soulmates! 💖💍"
        
    text = (
        f"💘 <b>Matchmaker Analysis</b>\n\n"
        f"👤 {mention_html(user.id, user.first_name)}\n"
        f"👤 {mention_html(target.id, target.first_name)}\n\n"
        f"<b>Result:</b> {percentage}%\n"
        f"<i>{comment}</i>"
    )
    
    await message.reply_html(text)

def register(app: Application):
    app.add_handler(CommandHandler("ship", ship))
