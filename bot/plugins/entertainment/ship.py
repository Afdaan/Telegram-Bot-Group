import random
import hashlib
import html
from telegram import Update
from telegram.constants import MessageEntityType
from telegram.ext import Application, CommandHandler, ContextTypes
from telegram.helpers import mention_html
from bot.utils.user_cache import get_user_id_by_username
from bot.database.repo import Repository
from bot.logger import get_logger

logger = get_logger(__name__)

async def _get_mentions(message):
    mentions = []
    
    if not message.entities:
        return mentions
        
    text_mentions = message.parse_entities([MessageEntityType.TEXT_MENTION])
    for entity, _ in text_mentions.items():
        if entity.user:
            mentions.append((entity.user.id, entity.user.first_name))

    mention_texts = message.parse_entities([MessageEntityType.MENTION])
    for _, mention_text in mention_texts.items():
        username = mention_text.lstrip("@").strip()
        if not username:
            continue
            
        user_id = get_user_id_by_username(username)
        if not user_id:
            db_user = await Repository.get_user_by_username(username)
            if db_user:
                user_id = db_user.telegram_id
        
        mentions.append((user_id, f"@{username}"))
        
    return mentions

def _format_mention(user_tuple):
    u_id, u_name = user_tuple
    if u_id is not None:
        return mention_html(u_id, u_name)
    return html.escape(u_name)

def _get_ship_comment(percentage):
    if percentage < 25:
        return "Awful match. 💔"
    if percentage < 50:
        return "Could work with effort. ✨"
    if percentage < 75:
        return "A solid couple! ❤️"
    if percentage < 90:
        return "Made for each other! 😍"
    return "Soulmates! 💖💍"

async def ship(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = update.effective_message
    sender = update.effective_user
    
    user_a = None
    user_b = None

    mentions = await _get_mentions(message)
    
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

    if not user_a or not user_b:
        await message.reply_text(
            "💘 <b>How to ship:</b>\n"
            "• Reply to someone\n"
            "• Mention one person\n"
            "• Mention two people\n"
            "Example: <code>/ship @user1 @user2</code>",
            parse_mode="HTML"
        )
        return

    identity_a = user_a[0] if user_a[0] is not None else user_a[1]
    identity_b = user_b[0] if user_b[0] is not None else user_b[1]

    if identity_a == identity_b:
        await message.reply_text("💘 You can't ship someone with themselves!")
        return

    sorted_identities = sorted([str(identity_a), str(identity_b)])
    seed_key = f"{sorted_identities[0]}_{sorted_identities[1]}_ship"
    ship_seed = int(hashlib.md5(seed_key.encode()).hexdigest(), 16)
    
    random.seed(ship_seed)
    percentage = random.randint(0, 100)
    random.seed()

    comment = _get_ship_comment(percentage)
    
    response_text = (
        f"💘 <b>Matchmaker Analysis</b>\n\n"
        f"👤 {_format_mention(user_a)}\n"
        f"👤 {_format_mention(user_b)}\n\n"
        f"<b>Result:</b> {percentage}%\n"
        f"<i>{comment}</i>"
    )

    logger.info(f"Ship analysis: {identity_a} x {identity_b} = {percentage}% in chat {update.effective_chat.id}")
    await message.reply_html(response_text)

def register(app: Application):
    app.add_handler(CommandHandler("ship", ship))
