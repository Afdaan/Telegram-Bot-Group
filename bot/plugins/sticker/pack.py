import io
from PIL import Image
from telegram import Update, InputSticker
from telegram.ext import Application, CommandHandler, ContextTypes
from telegram.error import TelegramError
from bot.database.repo import Repository
from bot.logger import get_logger

logger = get_logger(__name__)

async def get_pack_name(user_id: int, context: ContextTypes.DEFAULT_TYPE) -> str:
    bot_username = context.bot.username
    return f"pack_{user_id}_by_{bot_username}"

async def process_image(photo_file) -> io.BytesIO:
    photo_bytes = await photo_file.download_as_bytearray()
    image = Image.open(io.BytesIO(photo_bytes))
    image.thumbnail((512, 512), Image.LANCZOS)
    
    output = io.BytesIO()
    image.save(output, format="WEBP")
    output.seek(0)
    return output

async def kang(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    pack_name = await get_pack_name(user.id, context)
    pack_title = f"{user.first_name}'s Pack"
    
    reply = update.effective_message.reply_to_message
    if not reply:
        await update.effective_message.reply_text("Reply to a photo or sticker to kang it.")
        return

    file_obj = None
    emoji = "🤔"

    if reply.photo:
        file_obj = await reply.photo[-1].get_file()
    elif reply.sticker:
        file_obj = await reply.sticker.get_file()
        if reply.sticker.emoji:
            emoji = reply.sticker.emoji
    elif reply.document and reply.document.mime_type and reply.document.mime_type.startswith("image/"):
         file_obj = await reply.document.get_file()
    else:
        await update.effective_message.reply_text("Unsupported media type.")
        return

    msg = await update.effective_message.reply_text("Processing...")

    try:
        sticker_io = await process_image(file_obj)
        sticker_input = InputSticker(sticker=sticker_io, emoji_list=[emoji])

        try:
            await context.bot.add_sticker_to_set(
                user_id=user.id,
                name=pack_name,
                sticker=sticker_input
            )
        except TelegramError as e:
            if "Stickerset_invalid" in str(e):
                await context.bot.create_new_sticker_set(
                    user_id=user.id,
                    name=pack_name,
                    title=pack_title,
                    stickers=[sticker_input],
                    sticker_format="static"
                )
                
                await Repository.upsert_user(user.id, user.username, user.first_name)
                try:
                    await Repository.register_sticker_pack(pack_name, user.id)
                except Exception:
                    pass
            else:
                raise e
        
        sticker_set = await context.bot.get_sticker_set(name=pack_name)
        new_sticker = sticker_set.stickers[-1]
        
        await update.effective_message.reply_sticker(sticker=new_sticker.file_id)
        await msg.delete()

    except Exception as e:
        logger.error(f"Error kanging sticker: {e}")
        await msg.edit_text(f"Failed to process sticker: {e}")


async def delsticker(update: Update, context: ContextTypes.DEFAULT_TYPE):
    reply = update.effective_message.reply_to_message
    if not reply or not reply.sticker:
        await update.effective_message.reply_text("Reply to a sticker from your pack with /delsticker.")
        return

    try:
        await context.bot.delete_sticker_from_set(sticker=reply.sticker.file_id)
        await update.effective_message.reply_text("✅ Sticker removed from pack.")
    except Exception as e:
        await update.effective_message.reply_text(f"Failed to delete sticker: {e}")


def register(app: Application):
    app.add_handler(CommandHandler("kang", kang))
    app.add_handler(CommandHandler("sticker", kang))
    app.add_handler(CommandHandler("delsticker", delsticker))
