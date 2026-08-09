"""Модуль для команды для помощи"""

import ast
import traceback
import os

from aiogram import Router, types, Bot
from aiogram.filters import Command
from aiogram.utils.keyboard import InlineKeyboardBuilder

from modules import botdebug as d
from modules import filters

router: Router = Router()

def extract_functions(filepath):
    """
    Возвращает:
    [{'name':..., 'doc':..., 'path':...}]
    """
    results = []

    try:
        with open(filepath, "r", encoding="utf-8") as f:
            source = f.read()
    except Exception:
        return results

    try:
        tree = ast.parse(source)
    except SyntaxError:
        return results

    for node in ast.walk(tree):
        if isinstance(node, ast.AsyncFunctionDef):
            for dec in node.decorator_list:
                if (
                    isinstance(dec, ast.Call)
                    and isinstance(dec.func, ast.Attribute)
                    and dec.func.attr == "message"
                    and isinstance(dec.func.value, ast.Name)
                    and dec.func.value.id == "router"
                ):
                    results.append({
                        "name": node.name,
                        "doc": ast.get_docstring(node),
                        "path": filepath
                    })
    return results


def scan_project(path):
    """
    Сканирует каталог, возвращает структуру:
    { 'filename.py': [ {name, doc, path}, ... ] }
    """
    tree = {}

    if os.path.isfile(path) and path.endswith(".py"):
        funcs = extract_functions(path)
        if funcs:
            tree[os.path.basename(path)] = funcs
        return tree

    for root, _, files in os.walk(path):
        for fname in files:
            if fname.endswith(".py"):
                fpath = os.path.join(root, fname)
                funcs = extract_functions(fpath)
                if funcs:
                    tree[fname] = funcs

    return tree


# --- Загружаем код один раз при запуске ---
PROJECT_MAP = scan_project("./modules")

async def file_menu(callback: types.CallbackQuery, filename: str):
    """
    Меню функций в файле.
    """
    kb = InlineKeyboardBuilder()

    for func in PROJECT_MAP[filename]:
        kb.button(text=func["name"], callback_data=f"func:{filename}:{func['name']}")

    kb.button(text="⬅ Назад", callback_data="back:root")
    kb.adjust(1)

    await callback.message.edit_text(
        f"Файл: <b>{filename}</b>\nВыберите функцию:",
        parse_mode="html",
        reply_markup=kb.as_markup()
    )


async def function_doc(callback: types.CallbackQuery, filename: str, funcname: str):
    """
    Показывает docstring выбранной функции.
    """
    for func in PROJECT_MAP[filename]:
        if func["name"] == funcname:
            doc = func["doc"] or "(пусто)"

            kb = InlineKeyboardBuilder()
            kb.button(text="⬅ Назад", callback_data=f"file:{filename}")

            await callback.message.edit_text(
                f"<b>Файл:</b> {filename}\n"
                f"<b>Функция:</b> {funcname}\n"
                f"<b>Docstring:</b>\n\n{doc}",
                parse_mode="html",
                reply_markup=kb.as_markup()
            )
            return

@router.message(Command("help"))
@d.bugreport
@filters.only_private
async def start_menu(message: types.Message, bot: Bot):
    """
    Главное меню: список файлов.
    """
    kb = InlineKeyboardBuilder()

    for fname in PROJECT_MAP.keys():
        kb.button(text=fname, callback_data=f"file:{fname}")

    kb.adjust(1)

    await message.reply("Выберите файл:", reply_markup=kb.as_markup())

async def cb_file(call: types.CallbackQuery, bot):
    if call.data.startswith("file:"):
        _, filename = call.data.split(":", 1)
        await file_menu(call, filename)

async def cb_func(call: types.CallbackQuery, bot):
    if call.data.startswith("func:"):
        _, filename, funcname = call.data.split(":", 2)
        await function_doc(call, filename, funcname)

async def cb_back_root(call: types.CallbackQuery, bot):
    if call.data == "back:root":
        kb = InlineKeyboardBuilder()
        for fname in PROJECT_MAP.keys():
            kb.button(text=fname, callback_data=f"file:{fname}")
        kb.adjust(1)

        await call.message.edit_text(
            "Выберите файл:",
            reply_markup=kb.as_markup()
        )
