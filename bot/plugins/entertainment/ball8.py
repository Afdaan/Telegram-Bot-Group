import random
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

async def ball8(update: Update, context: ContextTypes.DEFAULT_TYPE):
    responses = [
        "It is certain.", "It is decidedly so.", "Without a doubt.",
        "Yes definitely.", "You may rely on it.", "As I see it, yes.",
        "Most likely.", "Outlook good.", "Yes.", "Signs point to yes.",
        "Reply hazy, try again.", "Ask again later.", "Better not tell you now.",
        "Cannot predict now.", "Concentrate and ask again.",
        "Don't count on it.", "My reply is no.", "My sources say no.",
        "Outlook not so good.", "Very doubtful."
    ]
    
    if not context.args:
        await update.effective_message.reply_text("Usage: /8ball <question>")
        return
        
    await update.effective_message.reply_html(f"🔮 <b>Magic 8-Ball:</b> {random.choice(responses)}")

def register(app: Application):
    app.add_handler(CommandHandler(["8ball", "ball8"], ball8))
