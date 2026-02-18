import html
import httpx
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes
from bot.logger import get_logger
from bot.config import settings

logger = get_logger(__name__)

async def trace_anime(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = update.effective_message
    
    target_msg = message.reply_to_message if message.reply_to_message else message
    
    photo = None
    if target_msg.photo:
        photo = target_msg.photo[-1]
    elif target_msg.sticker and not target_msg.sticker.is_animated and not target_msg.sticker.is_video:
        photo = target_msg.sticker
    elif target_msg.animation and target_msg.animation.thumbnail:
        photo = target_msg.animation.thumbnail
    elif target_msg.video and target_msg.video.thumbnail:
        photo = target_msg.video.thumbnail
    elif target_msg.video_note and target_msg.video_note.thumbnail:
        photo = target_msg.video_note.thumbnail
    elif target_msg.document and target_msg.document.mime_type.startswith("image/"):
        photo = target_msg.document

    if not photo:
        await message.reply_text("Please reply to an image, video, or sticker to find its source.")
        return

    args = context.args
    allow_nsfw = "-nsfw" in args
    force_manga = "-manga" in args
    force_anime = "-anime" in args
    
    status_msg = await message.reply_text("🔍 Searching for source...")

    try:
        file = await context.bot.get_file(photo.file_id)
        image_bytes = bytes(await file.download_as_bytearray())
        
        if not force_manga:
            res = await _search_tracemoe(image_bytes, allow_nsfw)
            if res and (res["similarity"] > 85 or force_anime):
                await _send_tracemoe_res(message, status_msg, res, allow_nsfw)
                return

        res = await _search_saucenao(image_bytes, allow_nsfw)
        if res and res["similarity"] > 60:
            await _send_saucenao_res(message, status_msg, res, allow_nsfw)
            return

        await status_msg.edit_text("❌ Could not find a reliable source (Anime or Manga).")

    except Exception as e:
        logger.error(f"Sauce search error: {e}")
        await status_msg.edit_text("❌ An error occurred while searching for the source.")

async def _search_tracemoe(image_bytes: bytes, allow_nsfw: bool):
    url = "https://api.trace.moe/search?cutBorders&anilistInfo"
    async with httpx.AsyncClient() as client:
        response = await client.post(url, files={"image": ("image.jpg", image_bytes, "image/jpeg")})
        if response.status_code != 200:
            return None
        data = response.json()
        if not data.get("result"):
            return None
        
        res = data["result"][0]
        res["similarity"] = round(res.get("similarity", 0) * 100, 2)
        return res

async def _send_tracemoe_res(message, status_msg, result, allow_nsfw):
    anilist = result.get("anilist", {})
    is_adult = anilist.get("isAdult", False)

    if is_adult and not allow_nsfw:
        await status_msg.edit_text("🔞 <b>NSFW content detected (Anime).</b>\nUse <code>/sauce -nsfw</code> to see this result.", parse_mode="HTML")
        return

    title = anilist.get("title", {}).get("romaji") or anilist.get("title", {}).get("native", "Unknown")
    episode = result.get("episode", "Movie/OVA")
    from_time = _format_time(result.get("from", 0))
    video_url = result.get("video")

    text = (
        f"🎬 <b>Anime Source Found!</b> ({result['similarity']}%)\n\n"
        f"📺 <b>Title:</b> {html.escape(title)}\n"
        f"🎞️ <b>Episode:</b> {episode}\n"
        f"⏱️ <b>Timestamp:</b> {from_time}"
    )
    if allow_nsfw and is_adult:
        text = "🔞 <b>NSFW Content Enabled</b>\n\n" + text

    if video_url:
        await message.reply_video(video_url, caption=text, parse_mode="HTML")
        await status_msg.delete()
    else:
        await status_msg.edit_text(text, parse_mode="HTML")

async def _search_saucenao(image_bytes: bytes, allow_nsfw: bool):
    params = {
        "output_type": 2,
        "testmode": 1,
        "numres": 1,
        "db": 999
    }
    if settings.saucenao_key:
        params["api_key"] = settings.saucenao_key

    url = "https://saucenao.com/search.php"
    async with httpx.AsyncClient() as client:
        files = {"file": ("image.jpg", image_bytes, "image/jpeg")}
        response = await client.post(url, params=params, files=files)
        if response.status_code != 200:
            return None
        data = response.json()
        
        results = data.get("results")
        if not results:
            return None
            
        res = results[0]
        res["similarity"] = float(res["header"]["similarity"])
        return res

async def _send_saucenao_res(message, status_msg, result, allow_nsfw):
    data = result["data"]
    header = result["header"]
    similarity = result["similarity"]
    
    title = data.get("title") or data.get("source") or "Unknown"
    
    meta = []
    if "eng_name" in data: meta.append(f"<b>ENG:</b> {data['eng_name']}")
    if "jp_name" in data: meta.append(f"<b>JP:</b> {data['jp_name']}")
    if "author" in data: meta.append(f"<b>Author:</b> {data['author']}")
    if "part" in data: meta.append(f"<b>Part/Chapter:</b> {data['part']}")
    
    links = data.get("ext_urls", [])
    
    text = (
        f"📖 <b>Manga/Art Source Found!</b> ({similarity}%)\n\n"
        f"📝 <b>Source:</b> {html.escape(title)}\n"
    )
    if meta:
        text += "\n".join(meta) + "\n"

    if allow_nsfw:
        text = "🔞 <b>NSFW Content Enabled</b>\n\n" + text

    if links:
        from telegram import InlineKeyboardButton, InlineKeyboardMarkup
        keyboard = InlineKeyboardMarkup([[InlineKeyboardButton("🔗 View Source", url=links[0])]])
        await status_msg.edit_text(text, reply_markup=keyboard, parse_mode="HTML")
    else:
        await status_msg.edit_text(text, parse_mode="HTML")

def _format_time(seconds: float) -> str:
    m, s = divmod(int(seconds), 60)
    h, m = divmod(m, 60)
    return f"{h:02d}:{m:02d}:{s:02d}" if h > 0 else f"{m:02d}:{s:02d}"

def register(app: Application):
    app.add_handler(CommandHandler(["sauce", "whatanime"], trace_anime))
