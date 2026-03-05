import html
import urllib.parse
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

async def qr_gen(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args and not (update.effective_message.reply_to_message and update.effective_message.reply_to_message.text):
        await update.effective_message.reply_html("🔍 <b>Usage:</b> <code>/qr &lt;text/link&gt;</code> or reply to a message.")
        return

    content = " ".join(context.args)
    if not content and update.effective_message.reply_to_message:
        content = update.effective_message.reply_to_message.text

    encoded_content = urllib.parse.quote(content)
    qr_url = f"https://api.qrserver.com/v1/create-qr-code/?size=300x300&data={encoded_content}"

    await update.effective_message.reply_photo(
        photo=qr_url,
        caption=f"✅ QR Code generated for: <code>{html.escape(content[:50])}...</code>",
        parse_mode="HTML"
    )

def register(app: Application):
    app.add_handler(CommandHandler(["qr", "qrcode"], qr_gen))
