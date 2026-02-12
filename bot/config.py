import os
from dataclasses import dataclass
from dotenv import load_dotenv

load_dotenv()


@dataclass(frozen=True)
class Settings:
    bot_token: str
    db_host: str
    db_port: int
    db_user: str
    db_password: str
    db_name: str
    log_level: str

    @property
    def database_url(self) -> str:
        return (
            f"mysql+aiomysql://{self.db_user}:{self.db_password}"
            f"@{self.db_host}:{self.db_port}/{self.db_name}"
        )


def load_settings() -> Settings:
    return Settings(
        bot_token=os.environ["BOT_TOKEN"],
        db_host=os.getenv("DB_HOST", "localhost"),
        db_port=int(os.getenv("DB_PORT", "3306")),
        db_user=os.getenv("DB_USER", "root"),
        db_password=os.getenv("DB_PASSWORD", ""),
        db_name=os.getenv("DB_NAME", "telegram_bot"),
        log_level=os.getenv("LOG_LEVEL", "INFO"),
    )


settings = load_settings()
