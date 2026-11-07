import ast
import html
import math
import operator
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

MAX_EXPRESSION_LENGTH = 200
MAX_AST_NODES = 50
MAX_ABS_RESULT = 10 ** 100
MAX_EXPONENT = 100

BIN_OPS = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.FloorDiv: operator.floordiv,
    ast.Pow: operator.pow,
}
UNARY_OPS = {
    ast.UAdd: operator.pos,
    ast.USub: operator.neg,
}


def _evaluate(node):
    if isinstance(node, ast.Expression):
        return _evaluate(node.body)
    if isinstance(node, ast.Constant) and type(node.value) in (int, float):
        if not math.isfinite(node.value) or abs(node.value) > MAX_ABS_RESULT:
            raise ValueError("Number is too large.")
        return node.value
    if isinstance(node, ast.UnaryOp) and type(node.op) in UNARY_OPS:
        return UNARY_OPS[type(node.op)](_evaluate(node.operand))
    if isinstance(node, ast.BinOp) and type(node.op) in BIN_OPS:
        left = _evaluate(node.left)
        right = _evaluate(node.right)
        if isinstance(node.op, ast.Pow) and abs(right) > MAX_EXPONENT:
            raise ValueError(f"Exponent must be between -{MAX_EXPONENT} and {MAX_EXPONENT}.")
        result = BIN_OPS[type(node.op)](left, right)
        if not isinstance(result, (int, float)) or not math.isfinite(result):
            raise ValueError("Result is not finite.")
        if abs(result) > MAX_ABS_RESULT:
            raise ValueError("Result is too large.")
        return result
    raise ValueError("Unsupported expression.")

async def calculate(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.effective_message.reply_html(
            "🔍 <b>Usage:</b> <code>/calc &lt;expression&gt;</code>\n"
            "<b>Example:</b> <code>/calc 2 + 2 * 5</code>"
        )
        return

    expression = "".join(context.args).replace(",", ".")

    if len(expression) > MAX_EXPRESSION_LENGTH:
        await update.effective_message.reply_text("Expression is too long.")
        return

    try:
        tree = ast.parse(expression, mode="eval")
        if sum(1 for _ in ast.walk(tree)) > MAX_AST_NODES:
            raise ValueError("Expression is too complex.")
        result = _evaluate(tree)
        await update.effective_message.reply_html(f"🔢 <b>Expression:</b> <code>{html.escape(expression)}</code>\n✅ <b>Result:</b> <code>{result}</code>")
    except (SyntaxError, TypeError, ValueError, ZeroDivisionError, OverflowError) as exc:
        await update.effective_message.reply_text(f"Error evaluating expression: {exc}")

def register(app: Application):
    app.add_handler(CommandHandler(["calc", "calculate"], calculate))
