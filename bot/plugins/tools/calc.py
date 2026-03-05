import html
import re
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

async def calculate(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.effective_message.reply_html(
            "🔍 <b>Usage:</b> <code>/calc &lt;expression&gt;</code>\n"
            "<b>Example:</b> <code>/calc 2 + 2 * 5</code>"
        )
        return

    expression = "".join(context.args).replace(",", ".")
    
    if not re.fullmatch(r"[0-9+\-*/().\s]+", expression):
        await update.effective_message.reply_text("Invalid characters in expression. Use only numbers and +-*/().")
        return

    try:
        result = eval(expression, {"__builtins__": None}, {})
        await update.effective_message.reply_html(f"🔢 <b>Expression:</b> <code>{html.escape(expression)}</code>\n✅ <b>Result:</b> <code>{result}</code>")
    except Exception as e:
        await update.effective_message.reply_text(f"Error evaluating expression: {e}")

def register(app: Application):
    app.add_handler(CommandHandler(["calc", "calculate"], calculate))
