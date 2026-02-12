import importlib
import pkgutil
from telegram.ext import Application
from bot.logger import get_logger

import bot.plugins

logger = get_logger(__name__)

PLUGIN_PACKAGES = [
    "bot.plugins.admin",
    "bot.plugins.sticker",
    "bot.plugins.group",
    "bot.plugins.setup",
    "bot.plugins.general",
]


def register_all_plugins(app: Application):
    loaded = 0

    for package_name in PLUGIN_PACKAGES:
        package = importlib.import_module(package_name)
        for importer, module_name, is_pkg in pkgutil.iter_modules(package.__path__):
            if is_pkg or module_name.startswith("_"):
                continue

            full_name = f"{package_name}.{module_name}"
            module = importlib.import_module(full_name)

            if hasattr(module, "register"):
                module.register(app)
                loaded += 1
            else:
                logger.warning("Skipped %s (no register function)", full_name)

    logger.info("Loaded %d plugins", loaded)
