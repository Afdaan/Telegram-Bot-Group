import io
from PIL import Image
from telegram import Update, InputSticker
from telegram.ext import Application, CommandHandler, ContextTypes
from bot.database.repo import Repository
from bot.utils.parse import extract_user


async def newpack(update: Update, context: ContextTypes.DEFAULT_TYPE):
    args = update.effective_message.text.split(maxsplit=1)
    if len(args) < 2:
        await update.effective_message.reply_text("Usage: /newpack <pack_title>")
        return

    title = args[1]
    user_id = update.effective_user.id
    bot_username = (await context.bot.get_me()).username

    pack_name = f"pack_{user_id}_by_{bot_username}"

    reply = update.effective_message.reply_to_message
    if not reply or not reply.photo:
        await update.effective_message.reply_text("Reply to a photo to use as the first sticker.")
        return

    photo = await reply.photo[-1].get_file()
    photo_bytes = await photo.download_as_bytearray()

    image = Image.open(io.BytesIO(photo_bytes))
    image.thumbnail((512, 512), Image.LANCZOS)
    output = io.BytesIO()
    image.save(output, format="WEBP")
    output.seek(0)

    sticker_input = InputSticker(
        sticker=output,
        emoji_list=["🤖"],
        format="static",
    )

    try:
        await context.bot.create_new_sticker_set(
            user_id=user_id,
            name=pack_name,
            title=title,
            stickers=[sticker_input],
        )
    except Exception as e:
        await update.effective_message.reply_text(f"Failed to create sticker pack: {e}")
        return

    await Repository.upsert_user(user_id)
    await Repository.register_sticker_pack(pack_name, user_id)

    await update.effective_message.reply_text(
        f"✅ Sticker pack created!\nhttps://t.me/addstickers/{pack_name}"
    )


async def addsticker(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    bot_username = (await context.bot.get_me()).username
    pack_name = f"pack_{user_id}_by_{bot_username}"

    reply = update.effective_message.reply_to_message
    if not reply or not reply.photo:
        await update.effective_message.reply_text("Reply to a photo with /addsticker to add it to your pack.")
        return

    photo = await reply.photo[-1].get_file()
    photo_bytes = await photo.download_as_bytearray()

    image = Image.open(io.BytesIO(photo_bytes))
    image.thumbnail((512, 512), Image.LANCZOS)
    output = io.BytesIO()
    image.save(output, format="WEBP")
    output.seek(0)

    sticker_input = InputSticker(
        sticker=output,
        emoji_list=["🤖"],
        format="static",
    )

    try:
        await context.bot.add_sticker_to_set(
            user_id=user_id,
            name=pack_name,
            sticker=sticker_input,
        )
    except Exception as e:
        await update.effective_message.reply_text(f"Failed to add sticker: {e}")
        return

    await update.effective_message.reply_text("✅ Sticker added to your pack.")


async def delsticker(update: Update, context: ContextTypes.DEFAULT_TYPE):
    reply = update.effective_message.reply_to_message
    if not reply or not reply.sticker:
        await update.effective_message.reply_text("Reply to a sticker from your pack with /delsticker.")
        return

    try:
        await context.bot.delete_sticker_from_set(sticker=reply.sticker.file_id)
    except Exception as e:
        await update.effective_message.reply_text(f"Failed to delete sticker: {e}")
        return

    await update.effective_message.reply_text("✅ Sticker removed from pack.")


def register(app: Application):
    app.add_handler(CommandHandler("newpack", newpack))
    app.add_handler(CommandHandler("addsticker", addsticker))
    app.add_handler(CommandHandler("delsticker", delsticker))
