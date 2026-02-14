import io
from PIL import Image
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes
from bot.logger import get_logger
from bot.plugins.sticker.utils import video_to_gif, video_to_webm

logger = get_logger(__name__)


async def tophoto(update: Update, context: ContextTypes.DEFAULT_TYPE):
    reply = update.effective_message.reply_to_message
    if not reply or not reply.sticker:
        await update.effective_message.reply_text("Reply to a sticker with /tophoto to convert it.")
        return

    if reply.sticker.is_animated or reply.sticker.is_video:
        await update.effective_message.reply_text(
            "⚠️ This is an animated/video sticker. Use /togif to convert it to a GIF."
        )
        return

    sticker_file = await reply.sticker.get_file()
    sticker_bytes = await sticker_file.download_as_bytearray()

    image = Image.open(io.BytesIO(sticker_bytes)).convert("RGBA")
    output = io.BytesIO()
    image.save(output, format="PNG")
    output.seek(0)
    output.name = "sticker.png"

    await update.effective_message.reply_photo(photo=output)


async def togif(update: Update, context: ContextTypes.DEFAULT_TYPE):
    reply = update.effective_message.reply_to_message
    if not reply or not reply.sticker:
        await update.effective_message.reply_text("Reply to a video/animated sticker with /togif to convert it.")
        return

    if not reply.sticker.is_video and not reply.sticker.is_animated:
        await update.effective_message.reply_text(
            "⚠️ This is a static sticker. Use /tophoto to convert it to PNG."
        )
        return

    msg = await update.effective_message.reply_text("⏳ Converting sticker to GIF...")

    sticker_file = await reply.sticker.get_file()
    sticker_bytes = await sticker_file.download_as_bytearray()

    gif_io = await video_to_gif(sticker_bytes)
    if not gif_io:
        await msg.edit_text("❌ Failed to convert sticker to GIF.")
        return

    await update.effective_message.reply_animation(animation=gif_io)
    await msg.delete()


async def tosticker(update: Update, context: ContextTypes.DEFAULT_TYPE):
    reply = update.effective_message.reply_to_message
    if not reply:
        await update.effective_message.reply_text("Reply to a GIF/animation with /tosticker to convert it.")
        return

    file_obj = None
    if reply.animation:
        file_obj = await reply.animation.get_file()
    elif reply.document and reply.document.mime_type in ("image/gif", "video/mp4"):
        file_obj = await reply.document.get_file()

    if not file_obj:
        await update.effective_message.reply_text(
            "Reply to a GIF/animation with /tosticker to convert it to a video sticker."
        )
        return

    msg = await update.effective_message.reply_text("⏳ Converting GIF to video sticker...")

    webm_io = await video_to_webm(file_obj)
    if not webm_io:
        await msg.edit_text("❌ Failed to convert GIF to video sticker. It may be too large.")
        return

    await update.effective_message.reply_sticker(sticker=webm_io)
    await msg.delete()


def register(app: Application):
    app.add_handler(CommandHandler("tophoto", tophoto))
    app.add_handler(CommandHandler("togif", togif))
    app.add_handler(CommandHandler("tosticker", tosticker))
