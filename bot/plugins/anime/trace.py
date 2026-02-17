import html
import httpx
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes
from bot.logger import get_logger

logger = get_logger(__name__)

async def trace_anime(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = update.effective_message
    
    target_msg = message.reply_to_message if message.reply_to_message else message
    
    photo = None
    if target_msg.photo:
        photo = target_msg.photo[-1]
    elif target_msg.sticker and not target_msg.sticker.is_animated and not target_msg.sticker.is_video:
        photo = target_msg.sticker
    elif target_msg.document and target_msg.document.mime_type.startswith("image/"):
        photo = target_msg.document

    if not photo:
        await message.reply_text("Please reply to an image or sticker to trace its anime source.")
        return

    status_msg = await message.reply_text("🔍 Searching for anime source...")

    try:
        file = await context.bot.get_file(photo.file_id)
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                "https://api.trace.moe/search?cutBorders&anilistInfo",
                files={"image": await file.download_as_bytearray()}
            )
            data = response.json()

        if response.status_code != 200 or not data.get("result"):
            await status_msg.edit_text("❌ Could not find any matching anime.")
            return

        result = data["result"][0]
        anilist = result.get("anilist", {})
        title_native = anilist.get("title", {}).get("native", "Unknown")
        title_romaji = anilist.get("title", {}).get("romaji", "Unknown")
        title_english = anilist.get("title", {}).get("english")
        
        episode = result.get("episode", "Movie/OVA")
        similarity = round(result.get("similarity", 0) * 100, 2)
        
        from_time = _format_time(result.get("from", 0))
        at_time = _format_time(result.get("at", 0))

        text = (
            f"🎬 <b>Source Found!</b> ({similarity}% match)\n\n"
            f"🇯🇵 <b>Native:</b> {html.escape(title_native)}\n"
            f"🏮 <b>Romaji:</b> {html.escape(title_romaji)}\n"
        )
        
        if title_english:
            text += f"🇺🇸 <b>English:</b> {html.escape(title_english)}\n"
            
        text += f"\n🎞️ <b>Episode:</b> {episode}\n"
        text += f"⏱️ <b>Timestamp:</b> {from_time} (Matched at {at_time})\n"
        
        video_url = result.get("video")
        if video_url:
            await message.reply_video(video_url, caption=text, parse_mode="HTML")
            await status_msg.delete()
        else:
            await status_msg.edit_text(text, parse_mode="HTML")

    except Exception as e:
        logger.error(f"Trace.moe error: {e}")
        await status_msg.edit_text("❌ An error occurred while tracing the image.")

def _format_time(seconds: float) -> str:
    m, s = divmod(int(seconds), 60)
    h, m = divmod(m, 60)
    return f"{h:02d}:{m:02d}:{s:02d}" if h > 0 else f"{m:02d}:{s:02d}"

def register(app: Application):
    app.add_handler(CommandHandler(["sauce", "whatanime"], trace_anime))
