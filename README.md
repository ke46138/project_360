# Project 360

![Static Badge](https://img.shields.io/badge/Python-%3E%3D3.10-yellow?style=flat-square)
![GitHub commit activity](https://img.shields.io/github/commit-activity/m/ke46138/Telegram_admin_bot?style=flat-square&color=2a5c03)

Модульный бот для администрирования групп и каналов в телеграме.

## Требования

- Сервер/компьютер готовый работать 24/7, желательно на Linux
- MySQL база данных
- Redis база данных
- API ключи для работы /ai, /ai_ds и /cat
- Белый IP адрес (для polling необязательно) или свой Telegram Bot API сервер
- Очень желательны знания Python и aiogram

## Настройка

0) В BotFather получить API ключ и включить inline mode.
1) Склонируйте репозиторий: `git clone https://github.com/ke46138/project_360.git` или если у вас настроен ssh ключ: `git clone git@github.com:ke46138/project_360.git`
2) Перейдите в папку репозитория: `cd project_360`
3) Установите все зависимости: `pip install -r requirements.txt`
4) Запустите бота: `python main.py` или `./main.py`
