import asyncio
import re
import sys
from pathlib import Path

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncEngine, create_async_engine

from bot.config import settings
from bot.logger import get_logger, setup_logging

logger = get_logger(__name__)
MIGRATION_DIR = Path(__file__).with_name("migrations")
IGNORABLE_MYSQL_CODES = {1050, 1060, 1061}


def _split_commands(content: str) -> list[str]:
    commands = []
    for command in content.split(";"):
        command = command.strip()
        if not command:
            continue
        upper = command.upper()
        if upper.startswith("CREATE DATABASE") or upper.startswith("USE "):
            continue
        commands.append(command)
    return commands


def _is_idempotent_duplicate(exc: Exception) -> bool:
    original = getattr(exc, "orig", exc)
    args = getattr(original, "args", ())
    if args and isinstance(args[0], int) and args[0] in IGNORABLE_MYSQL_CODES:
        return True
    message = str(exc).lower()
    return any(
        marker in message
        for marker in ("already exists", "duplicate column", "duplicate key name")
    )


async def _statement_already_applied(connection, command: str) -> bool:
    column_match = re.search(
        r"ALTER\s+TABLE\s+`?(\w+)`?\s+ADD\s+COLUMN\s+`?(\w+)`?",
        command,
        re.IGNORECASE,
    )
    if column_match:
        return bool(await connection.scalar(
            text("""
                SELECT 1
                FROM information_schema.columns
                WHERE table_schema = DATABASE()
                  AND table_name = :table_name
                  AND column_name = :column_name
            """),
            {
                "table_name": column_match.group(1),
                "column_name": column_match.group(2),
            },
        ))

    index_match = re.search(
        r"CREATE\s+(?:UNIQUE\s+)?INDEX\s+`?(\w+)`?\s+ON\s+`?(\w+)`?",
        command,
        re.IGNORECASE,
    )
    if index_match:
        return bool(await connection.scalar(
            text("""
                SELECT 1
                FROM information_schema.statistics
                WHERE table_schema = DATABASE()
                  AND table_name = :table_name
                  AND index_name = :index_name
            """),
            {
                "index_name": index_match.group(1),
                "table_name": index_match.group(2),
            },
        ))

    return False


async def run_migrations(database_engine: AsyncEngine | None = None) -> None:
    if not MIGRATION_DIR.is_dir():
        raise RuntimeError(f"Migration directory not found: {MIGRATION_DIR}")

    owns_engine = database_engine is None
    active_engine = database_engine or create_async_engine(settings.database_url, echo=False)

    try:
        async with active_engine.begin() as connection:
            await connection.execute(text("""
                CREATE TABLE IF NOT EXISTS schema_migrations (
                    migration VARCHAR(255) PRIMARY KEY,
                    applied_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
                ) ENGINE=InnoDB
            """))

        for migration_file in sorted(MIGRATION_DIR.glob("*.sql")):
            async with active_engine.begin() as connection:
                applied = await connection.scalar(
                    text("SELECT 1 FROM schema_migrations WHERE migration = :migration"),
                    {"migration": migration_file.name},
                )
                if applied:
                    continue

                commands = _split_commands(migration_file.read_text(encoding="utf-8"))
                for command in commands:
                    if await _statement_already_applied(connection, command):
                        continue
                    try:
                        await connection.execute(text(command))
                    except Exception as exc:
                        if not _is_idempotent_duplicate(exc):
                            raise RuntimeError(
                                f"Migration {migration_file.name} failed"
                            ) from exc

                await connection.execute(
                    text("INSERT INTO schema_migrations (migration) VALUES (:migration)"),
                    {"migration": migration_file.name},
                )
                logger.info("Applied migration %s", migration_file.name)
    finally:
        if owns_engine:
            await active_engine.dispose()


if __name__ == "__main__":
    setup_logging(settings.log_level)
    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(run_migrations())
