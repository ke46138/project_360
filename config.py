"""Модуль конфигурации бота.

Загружает переменные окружения, в том числе из файла .env при его наличии,
обеспечивая полную совместимость для запуска как в Docker, так и без него.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any, Set


def _load_dotenv(dotenv_path: Path | str | None = None) -> None:
    """Загружает переменные из .env файла в os.environ, если они ещё не установлены."""
    if dotenv_path is None:
        dotenv_path = Path(__file__).resolve().parent / ".env"
    else:
        dotenv_path = Path(dotenv_path)

    if not dotenv_path.is_file():
        return

    try:
        with open(dotenv_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
                if "=" in line:
                    key, val = line.split("=", 1)
                    key = key.strip()
                    val = val.strip().strip('"').strip("'")
                    if key and key not in os.environ:
                        os.environ[key] = val
    except OSError:
        pass


class _Config:
    """Хранилище конфигурации приложения."""

    PROJECT_NAME: str = "project_360"
    BOT_TOKEN: str = ""
    API_MODE: str = "polling"
    WEBHOOK_URL_FULL: str = ""
    WEBHOOK_URL: str = ""
    CUSTOM_BOT_API_ENABLED: bool = False
    BOT_API_SERVER: str = "https://api.telegram.org"
    HOST: str = "0.0.0.0"
    PORT: int = 8080

    DEVS: Set[int] = set()
    DEV_ADMIN_USERID: int = 0

    URL_ALLOWLIST: Set[str] = set()

    BOT_PATH: str = ""
    ABOUT_BOT_TEXT: str = "Тотальная Защита 360"

    MYSQL_HOST: str = "localhost"
    MYSQL_PORT: int = 3306
    MYSQL_USER: str = "root"
    MYSQL_PASSWORD: str = ""
    MYSQL_DATABASE: str = "admindb"

    AI_API_KEY: str = "NONE"
    CAT_API_KEY: str = "none"
    DS_KEY: str = "none"
    DS_CHATID: str = ""
    DS_MSGID: int = 2
    AI_MODEL: str = "google/gemini-2.0-flash-exp:free"
    AI_ENDPOINT: str = "https://openrouter.ai/api/v1"

    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    REDIS_USER: str = ""
    REDIS_PASSWORD: str = ""
    REDIS_DATABASE: int = 0

    def __init__(self) -> None:
        self.reload()

    def reload(self) -> None:
        """Перезагружает конфигурацию из файла .env и переменных окружения."""
        _load_dotenv()

        self.PROJECT_NAME = os.getenv("PROJECT_NAME", "project_360")
        self.BOT_TOKEN = os.getenv("BOT_TOKEN", "")
        self.API_MODE = os.getenv("API_MODE", "polling").strip().lower()
        self.WEBHOOK_URL_FULL = os.getenv("WEBHOOK_URL_FULL", "")
        self.WEBHOOK_URL = os.getenv("WEBHOOK_URL", "")
        self.CUSTOM_BOT_API_ENABLED = os.getenv("CUSTOM_BOT_API_ENABLED", "false").lower() == "true"
        self.BOT_API_SERVER = os.getenv("BOT_API_SERVER", "https://api.telegram.org")
        self.HOST = os.getenv("HOST", "0.0.0.0")
        self.PORT = int(os.getenv("PORT", "8080"))

        raw_devs = os.getenv("DEVS", "")
        self.DEVS = {int(x.strip()) for x in raw_devs.split(",") if x.strip().isdigit()}
        self.DEV_ADMIN_USERID = int(os.getenv("DEV_ADMIN_USERID", "0") or "0")

        raw_urls = os.getenv("URL_ALLOWLIST", "example.com")
        self.URL_ALLOWLIST = {x.strip().lower() for x in raw_urls.split(",") if x.strip()}

        self.BOT_PATH = os.getenv("BOT_PATH", str(Path(__file__).resolve().parent))
        self.ABOUT_BOT_TEXT = os.getenv(
            "ABOUT_BOT_TEXT",
            "Бот для администрирования групп и каналов в Telegram."
        )

        self.MYSQL_HOST = os.getenv("MYSQL_HOST", "localhost")
        self.MYSQL_PORT = int(os.getenv("MYSQL_PORT", "3306"))
        self.MYSQL_USER = os.getenv("MYSQL_USER", "root")
        self.MYSQL_PASSWORD = os.getenv("MYSQL_PASSWORD", "")
        self.MYSQL_DATABASE = os.getenv("MYSQL_DATABASE", "admindb")

        self.AI_API_KEY = os.getenv("AI_API_KEY", "NONE")
        self.CAT_API_KEY = os.getenv("CAT_API_KEY", "none")
        self.DS_KEY = os.getenv("DS_KEY", "none")
        self.DS_CHATID = os.getenv("DS_CHATID", "")
        self.DS_MSGID = int(os.getenv("DS_MSGID", "2"))
        self.AI_MODEL = os.getenv("AI_MODEL", "google/gemini-2.0-flash-exp:free")
        self.AI_ENDPOINT = os.getenv("AI_ENDPOINT", "https://openrouter.ai/api/v1")

        self.REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
        self.REDIS_PORT = int(os.getenv("REDIS_PORT", "6379"))
        self.REDIS_USER = os.getenv("REDIS_USER", "")
        self.REDIS_PASSWORD = os.getenv("REDIS_PASSWORD", "")
        self.REDIS_DATABASE = int(os.getenv("REDIS_DATABASE", "0"))


_config = _Config()


def reload() -> None:
    """Публичная функция перезагрузки конфигурации."""
    _config.reload()


def __getattr__(name: str) -> Any:
    """Делегирует доступ к атрибутам конфигурации."""
    return getattr(_config, name)
