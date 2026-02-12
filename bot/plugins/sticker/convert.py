import io
from PIL import Image
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes


async def sticker(update: Update, context: ContextTypes.DEFAULT_TYPE):
    reply = update.effective_message.reply_to_message
    if not reply or not reply.photo:
        await update.effective_message.reply_text("Reply to a photo with /sticker to convert it.")
        return

    photo = await reply.photo[-1].get_file()
    photo_bytes = await photo.download_as_bytearray()

    image = Image.open(io.BytesIO(photo_bytes))
    image.thumbnail((512, 512), Image.LANCZOS)

    output = io.BytesIO()
    image.save(output, format="WEBP")
    output.seek(0)
    output.name = "sticker.webp"

    await update.effective_message.reply_sticker(sticker=output)


async def tophoto(update: Update, context: ContextTypes.DEFAULT_TYPE):
    reply = update.effective_message.reply_to_message
    if not reply or not reply.sticker:
        await update.effective_message.reply_text("Reply to a sticker with /tophoto to convert it.")
        return

    if reply.sticker.is_animated or reply.sticker.is_video:
        await update.effective_message.reply_text("Animated/video stickers are not supported.")
        return

    sticker_file = await reply.sticker.get_file()
    sticker_bytes = await sticker_file.download_as_bytearray()

    image = Image.open(io.BytesIO(sticker_bytes)).convert("RGBA")

    output = io.BytesIO()
    image.save(output, format="PNG")
    output.seek(0)
    output.name = "sticker.png"

    await update.effective_message.reply_photo(photo=output)


def register(app: Application):
    app.add_handler(CommandHandler("sticker", sticker))
    app.add_handler(CommandHandler("tophoto", tophoto))
