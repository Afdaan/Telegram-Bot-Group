from telegram import Update
from telegram.ext import ApplicationBuilder
from bot.config import settings
from bot.logger import setup_logging, get_logger
from bot.database.engine import engine, init_db
from bot.plugins.loader import register_all_plugins
from bot.errors import error_handler
from migrate import run_migrations

logger = get_logger(__name__)


async def post_init(application):
    await run_migrations(engine)
    await init_db()
    logger.info("Database migrations and table sync complete")

    bot_info = await application.bot.get_me()
    logger.info("Bot online → @%s (id: %s)", bot_info.username, bot_info.id)


def main():
    setup_logging(settings.log_level)
    logger.info("Starting bot...")

    app = (
        ApplicationBuilder()
        .token(settings.bot_token)
        .connect_timeout(20)
        .read_timeout(20)
        .write_timeout(20)
        .get_updates_connect_timeout(20)
        .get_updates_read_timeout(65)
        .get_updates_write_timeout(20)
        .post_init(post_init)
        .build()
    )

    register_all_plugins(app)
    app.add_error_handler(error_handler)

    logger.info("Polling for updates")
    app.run_polling(
        allowed_updates=Update.ALL_TYPES,
        drop_pending_updates=True,
    )
