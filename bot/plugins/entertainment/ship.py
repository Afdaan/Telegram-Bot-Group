import random
import hashlib
from telegram import Update
from telegram.constants import MessageEntityType
from telegram.ext import Application, CommandHandler, ContextTypes
from telegram.helpers import mention_html
from bot.utils.parse import extract_user

async def ship(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = update.effective_message
    sender = update.effective_user
    
    user_a = None
    user_b = None

    mentions = []
    
    if message.entities:
        text_mentions = message.parse_entities([MessageEntityType.TEXT_MENTION])
        for entity, _ in text_mentions.items():
            if entity.user:
                mentions.append((entity.user.id, entity.user.first_name))

        mention_texts = message.parse_entities([MessageEntityType.MENTION])
        for _, mention_text in mention_texts.items():
            username = mention_text.lstrip("@").strip()
            from bot.utils.user_cache import get_user_id_by_username
            from bot.database.repo import Repository
            
            user_id = get_user_id_by_username(username)
            if not user_id:
                db_user = await Repository.get_user_by_username(username)
                if db_user:
                    user_id = db_user.telegram_id
            
            if user_id:
                mentions.append((user_id, f"@{username}"))

    if len(mentions) >= 2:
        user_a = mentions[0]
        user_b = mentions[1]
    elif len(mentions) == 1:
        if message.reply_to_message and not message.reply_to_message.forum_topic_created:
            user_a = mentions[0]
            reply_user = message.reply_to_message.from_user
            user_b = (reply_user.id, reply_user.first_name)
        else:
            user_a = (sender.id, sender.first_name)
            user_b = mentions[0]
    elif message.reply_to_message and not message.reply_to_message.forum_topic_created:
        user_a = (sender.id, sender.first_name)
        reply_user = message.reply_to_message.from_user
        user_b = (reply_user.id, reply_user.first_name)

    if not user_a or not user_b or user_a[0] == user_b[0]:
        await message.reply_text(
            "💘 <b>How to ship:</b>\n"
            "• Reply to someone\n"
            "• Mention one person\n"
            "• Mention two people\n"
            "Example: <code>/ship @user1 @user2</code>",
            parse_mode="HTML"
        )
        return

    ids = sorted([user_a[0], user_b[0]])
    seed_str = f"{ids[0]}_{ids[1]}_ship"
    seed = int(hashlib.md5(seed_str.encode()).hexdigest(), 16)
    
    random.seed(seed)
    percentage = random.randint(0, 100)
    random.seed()

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
        f"👤 {mention_html(user_a[0], user_a[1])}\n"
        f"👤 {mention_html(user_b[0], user_b[1])}\n\n"
        f"<b>Result:</b> {percentage}%\n"
        f"<i>{comment}</i>"
    )

    await message.reply_html(text)

def register(app: Application):
    app.add_handler(CommandHandler("ship", ship))
