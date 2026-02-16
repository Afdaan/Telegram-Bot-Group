import random
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes
from telegram.helpers import mention_html
from bot.utils.parse import extract_user

async def kill(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    target = await extract_user(update)
    
    kill_scenarios = [
        "stabbed {target} with a rusty spoon.",
        "pushed {target} into a pit of hungry alligators.",
        "sent {target} to the moon without a spacesuit.",
        "accidentally dropped a piano on {target}.",
        "hit {target} with a high-speed train.",
        "smothered {target} with a giant marshmallow.",
        "challenged {target} to a duel and won immediately.",
        "tricked {target} into drinking expired milk.",
        "bored {target} to death with a 10-hour lecture on grass."
    ]
    
    scenario = random.choice(kill_scenarios)
    
    if target:
        target_id, target_name = target
        action = scenario.format(target=mention_html(target_id, target_name))
        text = f"💀 {mention_html(user.id, user.first_name)} {action}"
    else:
        text = f"💀 {mention_html(user.id, user.first_name)} try to kill themselves but failed miserably."
        
    await update.effective_message.reply_html(text)

def register(app: Application):
    app.add_handler(CommandHandler("kill", kill))
