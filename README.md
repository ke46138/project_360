# Project 360

![Static Badge](https://img.shields.io/badge/Python-%3E%3D3.14-yellow?style=flat-square)

Модульный Telegram-бот для администрирования групп и каналов на базе `aiogram 3`.

## Требования

- Python >= 3.14 (или Docker)
- MySQL / MariaDB
- Redis
- API-ключи (Telegram Bot Token, OpenRouter/OpenAI, DeepSeek и TheCatAPI при использовании соответствующих команд)

## Настройка окружения

1. Получите токен бота в [@BotFather](https://t.me/BotFather) и включите inline mode (`/setinline`).
2. Скопируйте шаблон переменных окружения:
   ```bash
   cp .env.example .env
   ```
3. Заполните необходимые параметры в `.env` (токен бота, реквизиты MySQL и Redis).

## Запуск

### Вариант 1: Через Docker (рекомендуется)

Запуск через Docker Compose:
```bash
docker compose up -d --build
```

Просмотр логов:
```bash
docker compose logs -f
```

### Вариант 2: Без Docker

#### С использованием `uv` (рекомендуется):
```bash
uv sync
uv run python main.py
```

#### С использованием стандартного `pip`:
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python main.py
```
