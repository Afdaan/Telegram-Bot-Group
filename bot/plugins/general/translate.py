import asyncio
from functools import partial
from deep_translator import GoogleTranslator
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes
from bot.logger import get_logger

logger = get_logger(__name__)

POPULAR_LANGS = {
    "en": "English", "id": "Indonesian", "ja": "Japanese",
    "ko": "Korean", "zh-CN": "Chinese", "ar": "Arabic",
    "de": "German", "es": "Spanish", "fr": "French",
    "hi": "Hindi", "it": "Italian", "ms": "Malay",
    "nl": "Dutch", "pt": "Portuguese", "ru": "Russian",
    "th": "Thai", "tr": "Turkish", "vi": "Vietnamese",
}


def _translate(text: str, target: str, source: str = "auto") -> str:
    return GoogleTranslator(source=source, target=target).translate(text)


async def translate_async(text: str, target: str) -> str:
    loop = asyncio.get_running_loop()
    return await loop.run_in_executor(None, partial(_translate, text, target))


async def translate(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = update.effective_message
    args = message.text.split(None, 1)

    if not message.reply_to_message and len(args) < 2:
        langs = "  ".join(f"`{code}` {name}" for code, name in POPULAR_LANGS.items())
        await message.reply_text(
            "📝 **Translate**\n\n"
            "**Usage:**\n"
            "• Reply to a message: `/tr <lang>`\n"
            "• Inline: `/tr <lang> <text>`\n\n"
            f"**Languages:**\n{langs}\n\n"
            "_Use any language code from Google Translate_",
            parse_mode="Markdown",
        )
        return

    if message.reply_to_message:
        original = message.reply_to_message.text or message.reply_to_message.caption
        if not original:
            await message.reply_text("That message has no text to translate.")
            return
        target_lang = args[1].lower().strip() if len(args) >= 2 else "en"
    else:
        parts = args[1].split(None, 1)
        if len(parts) < 2:
            await message.reply_text("Usage: /tr <lang> <text>")
            return
        target_lang = parts[0].lower().strip()
        original = parts[1]

    try:
        result = await translate_async(original, target_lang)

        if not result or result.strip() == original.strip():
            await message.reply_text("No translation needed or same language detected.")
            return

        lang_name = POPULAR_LANGS.get(target_lang, target_lang.upper())
        await message.reply_text(
            f"🌐 <b>{lang_name}</b>\n{result}",
            parse_mode="HTML",
        )

    except Exception as e:
        error_msg = str(e).lower()
        if "not a valid" in error_msg or "not supported" in error_msg:
            await message.reply_text(f"❌ Unknown language code: `{target_lang}`", parse_mode="Markdown")
        else:
            await message.reply_text(f"❌ Translation failed: {e}")
            logger.error("TRANSLATE error: %s", e)


def register(app: Application):
    app.add_handler(CommandHandler(["tr", "translate"], translate))
