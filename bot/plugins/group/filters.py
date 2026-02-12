import shlex
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters as TelegramFilters, ContextTypes
from bot.database.repo import Repository
from bot.logger import get_logger
from bot.utils.decorators import group_only, admin_only

logger = get_logger(__name__)


@group_only
@admin_only
async def add_filter(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.effective_message.text
    rest = text.partition(' ')[2].strip()

    if not rest:
        await update.effective_message.reply_text("Usage: /filter <trigger> <response>")
        return

    trigger = ""
    response = ""
    
    if rest.startswith(('"', "'")):
        quote_char = rest[0]
        try:
            end_quote = rest.find(quote_char, 1)
            if end_quote == -1:
                raise ValueError("Unbalanced quotes")
            
            trigger = rest[1:end_quote]
            response = rest[end_quote+1:].strip()
        except Exception:
            await update.effective_message.reply_text("Error parsing quotes.")
            return
    else:
        parts = rest.split(' ', 1)
        trigger = parts[0]
        response = parts[1] if len(parts) > 1 else ""

    if not trigger:
        await update.effective_message.reply_text("Trigger cannot be empty.")
        return

    if not response and not update.effective_message.reply_to_message:
        await update.effective_message.reply_text("You must provide a response or reply to a message.")
        return

    file_id = None
    file_type = None
    
    if not response and update.effective_message.reply_to_message:
        reply = update.effective_message.reply_to_message
        if reply.text:
            response = reply.text
        elif reply.caption:
            response = reply.caption
            if reply.photo:
                file_id = reply.photo[-1].file_id
                file_type = "photo"
            elif reply.video:
                file_id = reply.video.file_id
                file_type = "video"
            elif reply.sticker:
                file_id = reply.sticker.file_id
                file_type = "sticker"
            elif reply.document:
                file_id = reply.document.file_id
                file_type = "document"
            elif reply.audio:
                file_id = reply.audio.file_id
                file_type = "audio"
            elif reply.voice:
                file_id = reply.voice.file_id
                file_type = "voice"
            elif reply.animation:
                file_id = reply.animation.file_id
                file_type = "animation"
        else:
            if reply.photo:
                file_id = reply.photo[-1].file_id
                file_type = "photo"
            elif reply.video:
                file_id = reply.video.file_id
                file_type = "video"
            elif reply.sticker:
                file_id = reply.sticker.file_id
                file_type = "sticker"
            elif reply.document:
                file_id = reply.document.file_id
                file_type = "document"
            elif reply.audio:
                file_id = reply.audio.file_id
                file_type = "audio"
            elif reply.voice:
                file_id = reply.voice.file_id
                file_type = "voice"
            elif reply.animation:
                file_id = reply.animation.file_id
                file_type = "animation"
            response = ""

    await Repository.upsert_group(update.effective_chat.id, update.effective_chat.title)

    await Repository.add_filter(
        group_id=update.effective_chat.id,
        trigger=trigger,
        response=response,
        file_id=file_id,
        file_type=file_type
    )

    await update.effective_message.reply_text(f"Filter saved: `{trigger}`", parse_mode="Markdown")


@group_only
@admin_only
async def stop_filter(update: Update, context: ContextTypes.DEFAULT_TYPE):
    args = context.args
    if not args:
        await update.effective_message.reply_text("Usage: /stop <trigger>")
        return

    trigger = update.effective_message.text.partition(' ')[2].strip()
    if trigger.startswith(('"', "'")) and trigger[-1] in ('"', "'"):
         trigger = trigger[1:-1]

    await Repository.upsert_group(update.effective_chat.id, update.effective_chat.title)
    
    deleted = await Repository.remove_filter(update.effective_chat.id, trigger)
    
    if deleted:
        await update.effective_message.reply_text(f"Filter deleted: `{trigger}`", parse_mode="Markdown")
    else:
        await update.effective_message.reply_text("Filter not found.")


@group_only
async def get_filters_list(update: Update, context: ContextTypes.DEFAULT_TYPE):
    filters_list = await Repository.get_filters(update.effective_chat.id)
    
    if not filters_list:
        await update.effective_message.reply_text("No filters in this group.")
        return

    text = "Filters in this group:\n"
    for f in filters_list:
        text += f"- `{f.trigger}`\n"
    
    await update.effective_message.reply_text(text, parse_mode="Markdown")


@group_only
async def filter_listener(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.effective_message or not update.effective_message.text:
        return

    text = update.effective_message.text.lower()
    chat_id = update.effective_chat.id
    
    filter_obj = await Repository.get_filter(chat_id, text)
    
    if filter_obj:
        if filter_obj.file_id:
            if filter_obj.file_type == "photo":
                await update.effective_message.reply_photo(filter_obj.file_id, caption=filter_obj.response)
            elif filter_obj.file_type == "video":
                await update.effective_message.reply_video(filter_obj.file_id, caption=filter_obj.response)
            elif filter_obj.file_type == "sticker":
                await update.effective_message.reply_sticker(filter_obj.file_id)
            elif filter_obj.file_type == "document":
                await update.effective_message.reply_document(filter_obj.file_id, caption=filter_obj.response)
            elif filter_obj.file_type == "audio":
                await update.effective_message.reply_audio(filter_obj.file_id, caption=filter_obj.response)
            elif filter_obj.file_type == "voice":
                await update.effective_message.reply_voice(filter_obj.file_id, caption=filter_obj.response)
            elif filter_obj.file_type == "animation":
                await update.effective_message.reply_animation(filter_obj.file_id, caption=filter_obj.response)
        elif filter_obj.response:
            await update.effective_message.reply_text(filter_obj.response)


def register(app: Application):
    app.add_handler(CommandHandler("filter", add_filter))
    app.add_handler(CommandHandler("stop", stop_filter))
    app.add_handler(CommandHandler("filters", get_filters_list))
    app.add_handler(MessageHandler(TelegramFilters.TEXT & ~TelegramFilters.COMMAND & TelegramFilters.ChatType.GROUPS, filter_listener))
