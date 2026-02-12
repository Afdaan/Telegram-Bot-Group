import logging
import sys
from logging.handlers import RotatingFileHandler
from pathlib import Path

LOG_DIR = Path("logs")
LOG_DIR.mkdir(exist_ok=True)

NOISY_LOGGERS = [
    "httpx",
    "httpcore",
    "hpack",
    "telegram.ext.Application",
    "telegram.ext.Updater",
    "telegram.ext.ExtBot",
    "apscheduler",
]

COLORS = {
    "DEBUG": "\033[36m",
    "INFO": "\033[32m",
    "WARNING": "\033[33m",
    "ERROR": "\033[31m",
    "CRITICAL": "\033[1;31m",
}
RESET = "\033[0m"
DIM = "\033[2m"


class ColorFormatter(logging.Formatter):

    def format(self, record):
        color = COLORS.get(record.levelname, "")
        level = f"{color}{record.levelname:<8}{RESET}"
        timestamp = f"{DIM}{self.formatTime(record, '%H:%M:%S')}{RESET}"
        name = self._short_name(record.name)
        msg = record.getMessage()

        formatted = f"  {timestamp}  {level}  {name}  {msg}"

        if record.exc_info and not record.exc_text:
            record.exc_text = self.formatException(record.exc_info)
        if record.exc_text:
            formatted += f"\n{record.exc_text}"

        return formatted

    @staticmethod
    def _short_name(name: str) -> str:
        parts = name.split(".")
        if len(parts) <= 2:
            return name
        return ".".join([p[0] for p in parts[:-1]] + [parts[-1]])


class FileFormatter(logging.Formatter):

    def __init__(self):
        super().__init__(
            fmt="%(asctime)s  %(levelname)-8s  %(name)s  %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )


def setup_logging(level: str = "INFO"):
    root = logging.getLogger()
    root.setLevel(getattr(logging, level.upper(), logging.INFO))

    if root.handlers:
        root.handlers.clear()

    console = logging.StreamHandler(sys.stdout)
    console.setFormatter(ColorFormatter())
    console.setLevel(logging.DEBUG)
    root.addHandler(console)

    file_handler = RotatingFileHandler(
        LOG_DIR / "bot.log",
        maxBytes=5 * 1024 * 1024,
        backupCount=3,
        encoding="utf-8",
    )
    file_handler.setFormatter(FileFormatter())
    file_handler.setLevel(logging.DEBUG)
    root.addHandler(file_handler)

    error_handler = RotatingFileHandler(
        LOG_DIR / "error.log",
        maxBytes=2 * 1024 * 1024,
        backupCount=3,
        encoding="utf-8",
    )
    error_handler.setFormatter(FileFormatter())
    error_handler.setLevel(logging.ERROR)
    root.addHandler(error_handler)

    for name in NOISY_LOGGERS:
        logging.getLogger(name).setLevel(logging.WARNING)


def get_logger(name: str) -> logging.Logger:
    return logging.getLogger(name)
