from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, filters, ContextTypes
from bot.database.repo import Repository
from bot.logger import get_logger
from bot.utils.decorators import group_only, admin_only

logger = get_logger(__name__)


@group_only
@admin_only
async def save_note(update: Update, context: ContextTypes.DEFAULT_TYPE):
    args = context.args
    if not args:
        await update.effective_message.reply_text("Usage: /save <note_name> (or reply to a message)")
        return

    note_name = args[0].lower()
    content = ""
    file_id = None
    file_type = None

    reply = update.effective_message.reply_to_message
    
    if reply:
        if reply.text:
            content = reply.text
        elif reply.caption:
            content = reply.caption
        
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
        if len(args) < 2:
            await update.effective_message.reply_text("Please provide content or reply to a message.")
            return
        content = " ".join(args[1:])

    await Repository.upsert_group(update.effective_chat.id, update.effective_chat.title)
    await Repository.add_note(
        group_id=update.effective_chat.id,
        name=note_name,
        content=content,
        file_id=file_id,
        file_type=file_type
    )

    logger.info("Note '#%s' saved in chat %s", note_name, update.effective_chat.id)
    await update.effective_message.reply_text(f"Note <code>#{note_name}</code> saved!", parse_mode="HTML")


@group_only
async def get_note(update: Update, context: ContextTypes.DEFAULT_TYPE):
    args = context.args
    if not args:
        await update.effective_message.reply_text("Usage: /get <note_name>")
        return

    note_name = args[0].lower()
    note = await Repository.get_note(update.effective_chat.id, note_name)

    if not note:
        await update.effective_message.reply_text("Note not found.")
        return

    await _send_note(update, note)


@group_only
@admin_only
async def clear_note(update: Update, context: ContextTypes.DEFAULT_TYPE):
    args = context.args
    if not args:
        await update.effective_message.reply_text("Usage: /clear <note_name>")
        return

    note_name = args[0].lower()
    deleted = await Repository.remove_note(update.effective_chat.id, note_name)

    if deleted:
        logger.info("Note '#%s' deleted in chat %s", note_name, update.effective_chat.id)
        await update.effective_message.reply_text(f"Note <code>#{note_name}</code> deleted.", parse_mode="HTML")
    else:
        await update.effective_message.reply_text("Note not found.")


@group_only
async def list_notes(update: Update, context: ContextTypes.DEFAULT_TYPE):
    notes = await Repository.get_notes(update.effective_chat.id)
    if not notes:
        await update.effective_message.reply_text("No notes saved in this group.")
        return

    text = f"✨ <b>Notes for {update.effective_chat.title}</b>\n\nYou can use <code>#notename</code> to recall them.\n"
    
    buttons = []
    sorted_notes = sorted(notes, key=lambda x: x.name)
    
    current_row = []
    for note in sorted_notes:
        current_row.append(InlineKeyboardButton(f"📎 {note.name}", callback_data=f"get_note:{note.name}"))
        if len(current_row) == 2:
            buttons.append(current_row)
            current_row = []
    if current_row:
        buttons.append(current_row)

    await update.effective_message.reply_text(text, parse_mode="HTML", reply_markup=InlineKeyboardMarkup(buttons))


async def note_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    note_name = query.data.split(":")[1]
    note = await Repository.get_note(update.effective_chat.id, note_name)
    
    if note:
        await _send_note(update, note)
        await query.answer()
    else:
        await query.answer("Note not found.", show_alert=True)


async def hashtag_listener(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.effective_message or not update.effective_message.text:
        return

    text = update.effective_message.text
    if not text.startswith("#") or len(text) < 2:
        return

    note_name = text.split()[0][1:].lower()
    note = await Repository.get_note(update.effective_chat.id, note_name)

    if note:
        await _send_note(update, note)


async def _send_note(update: Update, note):
    msg = update.effective_message
    reply_to = msg.reply_to_message.message_id if msg.reply_to_message else msg.message_id

    if note.file_id:
        if note.file_type == "photo":
            await msg.reply_photo(note.file_id, caption=note.content, reply_to_message_id=reply_to)
        elif note.file_type == "video":
            await msg.reply_video(note.file_id, caption=note.content, reply_to_message_id=reply_to)
        elif note.file_type == "sticker":
            await msg.reply_sticker(note.file_id, reply_to_message_id=reply_to)
        elif note.file_type == "document":
            await msg.reply_document(note.file_id, caption=note.content, reply_to_message_id=reply_to)
        elif note.file_type == "audio":
            await msg.reply_audio(note.file_id, caption=note.content, reply_to_message_id=reply_to)
        elif note.file_type == "voice":
            await msg.reply_voice(note.file_id, caption=note.content, reply_to_message_id=reply_to)
        elif note.file_type == "animation":
            await msg.reply_animation(note.file_id, caption=note.content, reply_to_message_id=reply_to)
    else:
        await msg.reply_text(note.content, reply_to_message_id=reply_to)


def register(app: Application):
    app.add_handler(CommandHandler("save", save_note))
    app.add_handler(CommandHandler("get", get_note))
    app.add_handler(CommandHandler("clear", clear_note))
    app.add_handler(CommandHandler("notes", list_notes))
    app.add_handler(CallbackQueryHandler(note_callback, pattern=r"^get_note:"))
    app.add_handler(MessageHandler(filters.TEXT & filters.ChatType.GROUPS, hashtag_listener))
