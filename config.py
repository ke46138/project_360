"""Модуль для загрузки конфигурации"""

import yaml
from typing import Any

CONFIG_FILE = "config.yml"

class _Config:
    """Хранилище конфигурации приложения"""

    PROJECT_NAME = "nodef"
    BOT_TOKEN = ""
    API_MODE = "polling"
    WEBHOOK_URL_FULL = ""
    WEBHOOK_URL = ""
    BOT_API_SERVER = "https://api.telegram.org"
    DEVS = {1234567890}
    HOST = ""
    PORT = 443
    DEV_ADMIN_USERID = 1234567890
    URL_ALLOWLIST = {"example.com"}
    BOT_PATH = "/home/user"
    ABOUT_BOT_TEXT = "nodef"
    MYSQL_HOST = "localhost"
    MYSQL_PORT = 3306
    MYSQL_USER = "root"
    MYSQL_PASSWORD = "hackme"
    MYSQL_DATABASE = "admindb"
    AI_API_KEY = "NONE"
    CAT_API_KEY = "none"
    DS_KEY = "none"
    DS_CHATID = ""
    DS_MSGID = 2
    AI_MODEL = "google/gemini-2.0-flash-exp:free"
    AI_ENDPOINT = "https://openrouter.ai/api/v1"

    REDIS_HOST = "localhost"
    REDIS_PORT = 6379
    REDIS_USER = "test"
    REDIS_PASSWORD = "hackme"
    REDIS_DATABASE = 0

    def reload(self) -> None:
        """Перезагружает конфигурацию из YAML файла"""

        with open(CONFIG_FILE, "r", encoding="utf-8") as file:
            data = yaml.safe_load(file)

        self.PROJECT_NAME = data["main"]["project_name"]
        self.BOT_TOKEN = data["main"]["bot_token"]
        self.API_MODE = data["main"]["api_mode"]
        self.WEBHOOK_URL_FULL = data["main"]["webhook_url_full"]
        self.WEBHOOK_URL = data["main"]["webhook_url"]
        self.CUSTOM_BOT_API_ENABLED = data["main"]["custom_bot_api_enabled"]
        self.BOT_API_SERVER = data["main"]["bot_api_server"]
        self.HOST = data["main"]["host"]
        self.DEVS = data["main"]["devs"]
        self.PORT = data["main"]["port"]
        self.DEV_ADMIN_USERID = data["main"]["dev_userid"]
        self.URL_ALLOWLIST = data["url_filter"]["allowlist"]
        self.BOT_PATH = data["main"]["bot_path"]
        self.ABOUT_BOT_TEXT = data["main"]["about_bot"]

        self.MYSQL_HOST = data["mysql_adapter"]["host"]
        self.MYSQL_PORT = data["mysql_adapter"]["port"]
        self.MYSQL_USER = data["mysql_adapter"]["user"]
        self.MYSQL_PASSWORD = data["mysql_adapter"]["password"]
        self.MYSQL_DATABASE = data["mysql_adapter"]["database"]

        self.AI_API_KEY = data["entertainment"]["ai_api_key"]
        self.CAT_API_KEY = data["entertainment"]["cat_api_key"]
        self.DS_KEY = data["entertainment"]["deepseek_api_key"]
        self.DS_CHATID = data["entertainment"]["deepseek_chatid"]
        self.DS_MSGID = data["entertainment"]["deepseek_msgid"]
        self.AI_MODEL = data["entertainment"]["ai_model"]
        self.AI_ENDPOINT = data["entertainment"]["ai_endpoint"]

        self.REDIS_HOST = data["redis"]["host"]
        self.REDIS_PORT = data["redis"]["port"]
        self.REDIS_USER = data["redis"]["user"]
        self.REDIS_PASSWORD = data["redis"]["password"]
        self.REDIS_DATABASE = data["redis"]["database"]

_config = _Config()

def reload() -> None:
    """Публичная функция перезагрузки конфигурации"""
    _config.reload()

def __getattr__(name: str) -> Any:
    """Делегирует доступ к атрибутам конфигурации"""
    return getattr(_config, name)
