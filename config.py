"""Модуль для загрузки конфигурации из переменных окружения"""

import os
from typing import Any

class _Config:
    """Хранилище конфигурации приложения"""

    PROJECT_NAME = os.getenv("PROJECT_NAME", "nodef")
    BOT_TOKEN = os.getenv("BOT_TOKEN", "")
    API_MODE = os.getenv("API_MODE", "polling")
    WEBHOOK_URL_FULL = os.getenv("WEBHOOK_URL_FULL", "")
    WEBHOOK_URL = os.getenv("WEBHOOK_URL", "")
    CUSTOM_BOT_API_ENABLED = os.getenv("CUSTOM_BOT_API_ENABLED", "false").lower() == "true"
    BOT_API_SERVER = os.getenv("BOT_API_SERVER", "https://api.telegram.org")
    HOST = os.getenv("HOST", "")
    PORT = int(os.getenv("PORT", "443"))

    DEVS = {int(x.strip()) for x in os.getenv("DEVS", "1234567890").split(",") if x.strip()}
    DEV_ADMIN_USERID = int(os.getenv("DEV_ADMIN_USERID", "1234567890"))

    URL_ALLOWLIST = {x.strip() for x in os.getenv("URL_ALLOWLIST", "example.com").split(",") if x.strip()}

    BOT_PATH = os.getenv("BOT_PATH", "/home/user")
    ABOUT_BOT_TEXT = os.getenv("ABOUT_BOT_TEXT", "nodef")

    MYSQL_HOST = os.getenv("MYSQL_HOST", "localhost")
    MYSQL_PORT = int(os.getenv("MYSQL_PORT", "3306"))
    MYSQL_USER = os.getenv("MYSQL_USER", "root")
    MYSQL_PASSWORD = os.getenv("MYSQL_PASSWORD", "hackme")
    MYSQL_DATABASE = os.getenv("MYSQL_DATABASE", "admindb")

    AI_API_KEY = os.getenv("AI_API_KEY", "NONE")
    CAT_API_KEY = os.getenv("CAT_API_KEY", "none")
    DS_KEY = os.getenv("DS_KEY", "none")
    DS_CHATID = os.getenv("DS_CHATID", "")
    DS_MSGID = int(os.getenv("DS_MSGID", "2"))
    AI_MODEL = os.getenv("AI_MODEL", "google/gemini-2.0-flash-exp:free")
    AI_ENDPOINT = os.getenv("AI_ENDPOINT", "https://openrouter.ai/api/v1")

    REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
    REDIS_PORT = int(os.getenv("REDIS_PORT", "6379"))
    REDIS_USER = os.getenv("REDIS_USER", "test")
    REDIS_PASSWORD = os.getenv("REDIS_PASSWORD", "hackme")
    REDIS_DATABASE = int(os.getenv("REDIS_DATABASE", "0"))

    def reload(self) -> None:
        """Перезагружает конфигурацию из переменных окружения"""
        load_dotenv(override=True)

        self.PROJECT_NAME = os.getenv("PROJECT_NAME", "nodef")
        self.BOT_TOKEN = os.getenv("BOT_TOKEN", "")
        self.API_MODE = os.getenv("API_MODE", "polling")
        self.WEBHOOK_URL_FULL = os.getenv("WEBHOOK_URL_FULL", "")
        self.WEBHOOK_URL = os.getenv("WEBHOOK_URL", "")
        self.CUSTOM_BOT_API_ENABLED = os.getenv("CUSTOM_BOT_API_ENABLED", "false").lower() == "true"
        self.BOT_API_SERVER = os.getenv("BOT_API_SERVER", "https://api.telegram.org")
        self.HOST = os.getenv("HOST", "")
        self.PORT = int(os.getenv("PORT", "443"))

        self.DEVS = {int(x.strip()) for x in os.getenv("DEVS", "1234567890").split(",") if x.strip()}
        self.DEV_ADMIN_USERID = int(os.getenv("DEV_ADMIN_USERID", "1234567890"))
        self.URL_ALLOWLIST = {x.strip() for x in os.getenv("URL_ALLOWLIST", "example.com").split(",") if x.strip()}

        self.BOT_PATH = os.getenv("BOT_PATH", "/home/user")
        self.ABOUT_BOT_TEXT = os.getenv("ABOUT_BOT_TEXT", "nodef")

        self.MYSQL_HOST = os.getenv("MYSQL_HOST", "localhost")
        self.MYSQL_PORT = int(os.getenv("MYSQL_PORT", "3306"))
        self.MYSQL_USER = os.getenv("MYSQL_USER", "root")
        self.MYSQL_PASSWORD = os.getenv("MYSQL_PASSWORD", "hackme")
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
        self.REDIS_USER = os.getenv("REDIS_USER", "test")
        self.REDIS_PASSWORD = os.getenv("REDIS_PASSWORD", "hackme")
        self.REDIS_DATABASE = int(os.getenv("REDIS_DATABASE", "0"))

_config = _Config()

def reload() -> None:
    """Публичная функция перезагрузки конфигурации"""
    _config.reload()

def __getattr__(name: str) -> Any:
    """Делегирует доступ к атрибутам конфигурации"""
    return getattr(_config, name)