import logging
import sys



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

def setup_logging(level: str = "INFO"):
    root = logging.getLogger()
    root.setLevel(getattr(logging, level.upper(), logging.INFO))

    if root.handlers:
        root.handlers.clear()

    console = logging.StreamHandler(sys.stdout)
    console.setFormatter(ColorFormatter())
    console.setLevel(logging.DEBUG)
    root.addHandler(console)

    for name in NOISY_LOGGERS:
        logging.getLogger(name).setLevel(logging.WARNING)


def get_logger(name: str) -> logging.Logger:
    return logging.getLogger(name)
