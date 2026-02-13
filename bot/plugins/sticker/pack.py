import io
import re
from PIL import Image
from telegram import Update, InputSticker, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, ContextTypes
from telegram.error import TelegramError
from bot.database.repo import Repository
from bot.logger import get_logger

logger = get_logger(__name__)

DEFAULT_EMOJI = "\U0001f604"


def sanitize_pack_name(name: str) -> str:
    cleaned = re.sub(r'[^a-zA-Z0-9_]', '', name.replace(' ', '_'))
    cleaned = re.sub(r'_+', '_', cleaned).strip('_')
    return cleaned[:40] or "pack"


async def get_default_pack_name(user_id: int, context: ContextTypes.DEFAULT_TYPE) -> str:
    return f"pack_{user_id}_by_{context.bot.username}"


async def get_named_pack_name(user_id: int, name: str, context: ContextTypes.DEFAULT_TYPE) -> str:
    clean = sanitize_pack_name(name)
    return f"{clean}_{user_id}_by_{context.bot.username}"


async def process_image(photo_file) -> io.BytesIO:
    photo_bytes = await photo_file.download_as_bytearray()
    image = Image.open(io.BytesIO(photo_bytes)).convert("RGBA")

    width, height = image.size
    if width >= height:
        new_width = 512
        new_height = max(1, int((512 / width) * height))
    else:
        new_height = 512
        new_width = max(1, int((512 / height) * width))

    image = image.resize((new_width, new_height), Image.LANCZOS)

    output = io.BytesIO()
    image.save(output, format="WEBP")
    output.seek(0)
    return output


async def extract_file(reply) -> tuple:
    file_obj = None
    emoji = DEFAULT_EMOJI

    if reply.photo:
        file_obj = await reply.photo[-1].get_file()
    elif reply.sticker:
        if reply.sticker.is_animated or reply.sticker.is_video:
            return None, emoji
        file_obj = await reply.sticker.get_file()
        if reply.sticker.emoji:
            emoji = reply.sticker.emoji
    elif reply.document and reply.document.mime_type and reply.document.mime_type.startswith("image/"):
        file_obj = await reply.document.get_file()

    return file_obj, emoji


def make_sticker(sticker_io: io.BytesIO, emoji: str) -> InputSticker:
    return InputSticker(sticker=sticker_io, emoji_list=[emoji], format="static")


async def require_pack_or_onboard(update: Update, context: ContextTypes.DEFAULT_TYPE) -> bool:
    if update.effective_chat.type == "private":
        return True

    user = update.effective_user
    packs = await Repository.get_user_sticker_packs(user.id)
    if packs:
        return True

    bot_username = context.bot.username
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton(
            "\U0001f4e6 Create Your First Pack",
            url=f"https://t.me/{bot_username}?start=newpack",
        )]
    ])
    await update.effective_message.reply_text(
        f"\U0001f44b Hey {user.first_name}! You don't have a sticker pack yet.\n\n"
        "DM me first to create your pack, then you can use /kang and /addsticker here!",
        reply_markup=keyboard,
    )
    return False


async def kang(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await require_pack_or_onboard(update, context):
        return

    user = update.effective_user
    packs = await Repository.get_user_sticker_packs(user.id)

    if packs:
        pack_name = packs[0].pack_name
        try:
            sticker_set = await context.bot.get_sticker_set(name=pack_name)
            pack_title = sticker_set.title
        except TelegramError:
            pack_name = await get_default_pack_name(user.id, context)
            pack_title = f"{user.first_name}'s Pack"
    else:
        pack_name = await get_default_pack_name(user.id, context)
        pack_title = f"{user.first_name}'s Pack"

    reply = update.effective_message.reply_to_message
    if not reply:
        await update.effective_message.reply_text("Reply to a photo or sticker to kang it.")
        return

    file_obj, emoji = await extract_file(reply)
    if not file_obj:
        await update.effective_message.reply_text("Unsupported media type. (animated/video stickers are not supported)")
        return

    if context.args:
        emoji = context.args[0]

    msg = await update.effective_message.reply_text("\u23f3 Kanging...")

    try:
        sticker_io = await process_image(file_obj)
        sticker_input = make_sticker(sticker_io, emoji)

        try:
            await context.bot.add_sticker_to_set(
                user_id=user.id,
                name=pack_name,
                sticker=sticker_input,
            )
        except TelegramError as e:
            if "STICKERSET_INVALID" in str(e).upper():
                await context.bot.create_new_sticker_set(
                    user_id=user.id,
                    name=pack_name,
                    title=pack_title,
                    stickers=[sticker_input],
                )
                await Repository.upsert_user(user.id, user.username, user.first_name)
                try:
                    await Repository.register_sticker_pack(pack_name, user.id)
                except Exception:
                    pass
            else:
                raise e

        sticker_set = await context.bot.get_sticker_set(name=pack_name)
        await update.effective_message.reply_sticker(sticker=sticker_set.stickers[-1].file_id)
        await msg.delete()

    except Exception as e:
        logger.error(f"Error kanging sticker: {e}")
        await msg.edit_text(f"Failed: {e}")


async def newpack(update: Update, context: ContextTypes.DEFAULT_TYPE):
    args = update.effective_message.text.split(maxsplit=1)
    if len(args) < 2:
        await update.effective_message.reply_text(
            "Usage: /newpack <pack_name>\n"
            "Reply to a photo or sticker as the first sticker."
        )
        return

    user = update.effective_user
    pack_title = args[1]
    pack_name = await get_named_pack_name(user.id, pack_title, context)

    reply = update.effective_message.reply_to_message
    if not reply:
        await update.effective_message.reply_text("Reply to a photo or sticker as the first sticker.")
        return

    file_obj, emoji = await extract_file(reply)
    if not file_obj:
        await update.effective_message.reply_text("Unsupported media type.")
        return

    msg = await update.effective_message.reply_text("\u23f3 Creating pack...")

    try:
        sticker_io = await process_image(file_obj)
        sticker_input = make_sticker(sticker_io, emoji)

        await context.bot.create_new_sticker_set(
            user_id=user.id,
            name=pack_name,
            title=pack_title,
            stickers=[sticker_input],
        )

        await Repository.upsert_user(user.id, user.username, user.first_name)
        try:
            await Repository.register_sticker_pack(pack_name, user.id)
        except Exception:
            pass

        sticker_set = await context.bot.get_sticker_set(name=pack_name)
        await update.effective_message.reply_sticker(sticker=sticker_set.stickers[-1].file_id)
        await msg.delete()

    except TelegramError as e:
        error_str = str(e).upper()
        if "NAME_OCCUPIED" in error_str or "ALREADY OCCUPIED" in error_str:
            await msg.edit_text("Pack name already taken. Try a different name.")
        else:
            logger.error(f"Error creating pack: {e}")
            await msg.edit_text(f"Failed: {e}")
    except Exception as e:
        logger.error(f"Error creating pack: {e}")
        await msg.edit_text(f"Failed: {e}")


async def addsticker(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await require_pack_or_onboard(update, context):
        return

    args = update.effective_message.text.split(maxsplit=1)
    if len(args) < 2:
        await update.effective_message.reply_text(
            "Usage: /addsticker <pack_name>\n"
            "Reply to a photo or sticker to add it."
        )
        return

    user = update.effective_user
    raw_args = args[1]
    split_args = raw_args.split(maxsplit=1)

    pack_title = raw_args
    custom_emoji = None

    if re.fullmatch(r'[^a-zA-Z0-9_]+', split_args[0]):
        custom_emoji = split_args[0]
        pack_title = split_args[1] if len(split_args) > 1 else ""

    pack_name = await get_named_pack_name(user.id, pack_title, context)

    reply = update.effective_message.reply_to_message
    if not reply:
        await update.effective_message.reply_text("Reply to a photo or sticker to add it.")
        return

    file_obj, emoji = await extract_file(reply)
    if not file_obj:
        await update.effective_message.reply_text("Unsupported media type.")
        return

    if custom_emoji:
        emoji = custom_emoji

    msg = await update.effective_message.reply_text("\u23f3 Adding sticker...")

    try:
        sticker_io = await process_image(file_obj)
        sticker_input = make_sticker(sticker_io, emoji)

        try:
            await context.bot.add_sticker_to_set(
                user_id=user.id,
                name=pack_name,
                sticker=sticker_input,
            )
        except TelegramError as e:
            if "STICKERSET_INVALID" in str(e).upper():
                await context.bot.create_new_sticker_set(
                    user_id=user.id,
                    name=pack_name,
                    title=pack_title,
                    stickers=[sticker_input],
                )
                await Repository.upsert_user(user.id, user.username, user.first_name)
                try:
                    await Repository.register_sticker_pack(pack_name, user.id)
                except Exception:
                    pass
            else:
                raise e

        sticker_set = await context.bot.get_sticker_set(name=pack_name)
        await update.effective_message.reply_sticker(sticker=sticker_set.stickers[-1].file_id)
        await msg.delete()

    except Exception as e:
        logger.error(f"Error adding sticker: {e}")
        await msg.edit_text(f"Failed: {e}")


async def delsticker(update: Update, context: ContextTypes.DEFAULT_TYPE):
    reply = update.effective_message.reply_to_message
    if not reply or not reply.sticker:
        await update.effective_message.reply_text("Reply to a sticker from your pack.")
        return

    try:
        await context.bot.delete_sticker_from_set(sticker=reply.sticker.file_id)
        await update.effective_message.reply_text("\u2705 Sticker removed from pack.")
    except Exception as e:
        await update.effective_message.reply_text(f"Failed: {e}")


async def mypacks(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    packs = await Repository.get_user_sticker_packs(user.id)

    if not packs:
        await update.effective_message.reply_text("You have no sticker packs.")
        return

    text = "\U0001f3a8 Your sticker packs:\n\n"
    for pack in packs:
        text += f"\u2022 [{pack.pack_name}](https://t.me/addstickers/{pack.pack_name})\n"

    await update.effective_message.reply_text(text, parse_mode="Markdown", disable_web_page_preview=True)


def register(app: Application):
    app.add_handler(CommandHandler("kang", kang))
    app.add_handler(CommandHandler("sticker", kang))
    app.add_handler(CommandHandler("newpack", newpack))
    app.add_handler(CommandHandler("addsticker", addsticker))
    app.add_handler(CommandHandler("delsticker", delsticker))
    app.add_handler(CommandHandler("mypacks", mypacks))
