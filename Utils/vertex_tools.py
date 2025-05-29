from __future__ import annotations
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from vertex import Vertex

import FunPayAPI.types

import time
from account_rental.db import get_all_rented_accounts, release_account
from datetime import datetime
import Utils.exceptions
import itertools
import psutil
import json
import sys
import os
import re


PHOTO_RE = re.compile(r'\$photo=[\d]+')
ENTITY_RE = re.compile(r"\$photo=\d+|\$new|(\$sleep=(\d+\.\d+|\d+))")


def count_products(path: str) -> int:
    """
    Считает кол-во товара в указанном файле.

    :param path: путь до файла с товарами.

    :return: кол-во товара в указанном файле.
    """
    if not os.path.exists(path):
        return 0
    with open(path, "r", encoding="utf-8") as f:
        products = f.read()
    products = products.split("\n")
    products = list(itertools.filterfalse(lambda el: not el, products))
    return len(products)


def cache_blacklist(blacklist: list[str]) -> None:
    """
    Кэширует черный список.

    :param blacklist: черный список.
    """
    if not os.path.exists("storage/cache"):
        os.makedirs("storage/cache")

    with open("storage/cache/blacklist.json", "w", encoding="utf-8") as f:
        f.write(json.dumps(blacklist, indent=4))


def load_blacklist() -> list[str]:
    """
    Загружает черный список.

    :return: черный список.
    """
    if not os.path.exists("storage/cache/blacklist.json"):
        return []

    with open("storage/cache/blacklist.json", "r", encoding="utf-8") as f:
        blacklist = f.read()

        try:
            blacklist = json.loads(blacklist)
        except json.decoder.JSONDecodeError:
            return []
        return blacklist


#def cache_disabled_plugins(disabled_plugins: list[str]) -> None:
#    """
#    Кэширует UUID отключенных плагинов.
#
#    :param disabled_plugins: список UUID отключенных плагинов.
#    """
#    if not os.path.exists("storage/cache"):
#        os.makedirs("storage/cache")
#
#    with open("storage/cache/disabled_plugins.json", "w", encoding="utf-8") as f:
#        f.write(json.dumps(disabled_plugins))


#def load_disabled_plugins() -> list[str]:
#    """
#    Загружает список UUID отключенных плагинов из кэша.
#
#    :return: список UUID отключенных плагинов.
#    """
#    if not os.path.exists("storage/cache/disabled_plugins.json"):
#        return []
#
#    with open("storage/cache/disabled_plugins.json", "r", encoding="utf-8") as f:
#        try:
#            return json.loads(f.read())
#        except json.decoder.JSONDecodeError:
#            return []


def cache_old_users(old_users: list[int]):
    """
    Сохраняет в кэш список пользователей, которые уже писали на аккаунт.
    """
    if not os.path.exists("storage/cache"):
        os.makedirs("storage/cache")
    with open(f"storage/cache/old_users.json", "w", encoding="utf-8") as f:
        f.write(json.dumps(old_users, ensure_ascii=False))


def load_old_users() -> list[int]:
    """
    Загружает из кэша список пользователей, которые уже писали на аккаунт.

    :return: список ID чатов.
    """
    if not os.path.exists(f"storage/cache/old_users.json"):
        return []
    with open(f"storage/cache/old_users.json", "r", encoding="utf-8") as f:
        users = f.read()
    return json.loads(users)


def create_greeting_text(vertex: Vertex):
    """
    Генерирует приветствие для вывода в консоль после загрузки данных о пользователе.
    """
    account = vertex.account
    balance = vertex.balance
    current_time = datetime.now()
    if current_time.hour < 4:
        greetings = "Какая прекрасная ночь"
    elif current_time.hour < 12:
        greetings = "Доброе утро"
    elif current_time.hour < 17:
        greetings = "Добрый день"
    else:
        greetings = "Добрый вечер"

    lines = [
        f"* {greetings}, $CYAN{account.username}.",
        f"* Ваш ID: $YELLOW{account.id}.",
        f"* Ваш текущий баланс: $CYAN{balance.total_rub} RUB $RESET| $MAGENTA{balance.total_usd} USD $RESET| $YELLOW{balance.total_eur} EUR",
        f"* Текущие незавершенные сделки: $YELLOW{account.active_sales}.",
        f"* Удачной торговли!"
    ]

    length = 60
    greetings_text = f"\n{'-'*length}\n"
    for line in lines:
        greetings_text += line + " "*(length - len(line.replace("$CYAN", "").replace("$YELLOW", "").replace("$MAGENTA", "").replace("$RESET", "")) - 1) + "$RESET*\n"
    greetings_text += f"{'-'*length}\n"
    return greetings_text


def time_to_str(time_: int):
    """
    Конвертирует число в строку формата "Хд Хч Хмин Хсек"

    :param time_: число для конвертации.

    :return: строку-время.
    """
    days = time_ // 86400
    hours = (time_ - days * 86400) // 3600
    minutes = (time_ - days * 86400 - hours * 3600) // 60
    seconds = time_ - days * 86400 - hours * 3600 - minutes * 60

    if not any([days, hours, minutes, seconds]):
        return "0 сек"
    time_str = ""
    if days:
        time_str += f"{days}д"
    if hours:
        time_str += f" {hours}ч"
    if minutes:
        time_str += f" {minutes}мин"
    if seconds:
        time_str += f" {seconds}сек"
    return time_str.strip()


def get_month_name(month_number: int) -> str:
    """
    Возвращает название месяца в родительном падеже.

    :param month_number: номер месяца.

    :return: название месяца в родительном падеже.
    """
    months = [
        "Января", "Февраля", "Марта",
        "Апреля", "Мая", "Июня",
        "Июля", "Августа", "Сентября",
        "Октября", "Ноября", "Декабря"
    ]
    if month_number > len(months):
        return months[0]
    return months[month_number-1]


def get_products(path: str, amount: int = 1) -> list[list[str] | int] | None:
    """
    Берет из товарного файла товар/-ы, удаляет их из товарного файла.

    :param path: путь до файла с товарами.
    :param amount: кол-во товара.

    :return: [[Товар/-ы], оставшееся кол-во товара]
    """
    with open(path, "r", encoding="utf-8") as f:
        products = f.read()

    products = products.split("\n")

    # Убираем пустые элементы
    products = list(itertools.filterfalse(lambda el: not el, products))

    if not products:
        raise Utils.exceptions.NoProductsError(path)

    elif len(products) < amount:
        raise Utils.exceptions.NotEnoughProductsError(path, len(products), amount)

    got_products = products[:amount]
    save_products = products[amount:]
    amount = len(save_products)

    with open(path, "w", encoding="utf-8") as f:
        f.write("\n".join(save_products))

    return [got_products, amount]


def add_products(path: str, products: list[str], at_zero_position=False):
    """
    Добавляет товары в файл с товарами.

    :param path: путь до файла с товарами.
    :param products: товары.
    :param at_zero_position: добавить товары в начало товарного файла.
    """
    if not at_zero_position:
        with open(path, "a", encoding="utf-8") as f:
            f.write("\n"+"\n".join(products))
    else:
        with open(path, "r", encoding="utf-8") as f:
            text = f.read()
        with open(path, "w", encoding="utf-8") as f:
            f.write("\n".join(products) + "\n" + text)


def format_msg_text(text: str, obj: FunPayAPI.types.Message | FunPayAPI.types.ChatShortcut) -> str:
    """
    Форматирует текст, подставляя значения переменных, доступных для MessageEvent.

    :param text: текст для форматирования.
    :param obj: экземпляр types.Message или types.ChatShortcut.

    :return: форматированый текст.
    """
    date_obj = datetime.now()
    month_name = get_month_name(date_obj.month)
    date = date_obj.strftime("%d.%m.%Y")
    str_date = f"{date_obj.day} {month_name}"
    str_full_date = str_date + f" {date_obj.year} года"

    time_ = date_obj.strftime("%H:%M")
    time_full = date_obj.strftime("%H:%M:%S")

    username = obj.author if isinstance(obj, FunPayAPI.types.Message) else obj.name
    chat_id = str(obj.chat_id) if isinstance(obj, FunPayAPI.types.Message) else str(obj.id)

    variables = {
        "$full_date_text": str_full_date,
        "$date_text": str_date,
        "$date": date,
        "$time": time_,
        "$full_time": time_full,
        "$username": username,
        "$message_text": str(obj),
        "$chat_id": chat_id
    }

    for var in variables:
        text = text.replace(var, variables[var])
    return text


def format_order_text(text: str, order: FunPayAPI.types.OrderShortcut | FunPayAPI.types.Order) -> str:
    """
    Форматирует текст, подставляя значения переменных, доступных для Order.

    :param text: текст для форматирования.
    :param order: экземпляр Order.

    :return: форматированый текст.
    """
    date_obj = datetime.now()
    month_name = get_month_name(date_obj.month)
    date = date_obj.strftime("%d.%m.%Y")
    str_date = f"{date_obj.day} {month_name}"
    str_full_date = str_date + f" {date_obj.year} года"

    time_ = date_obj.strftime("%H:%M")
    time_full = date_obj.strftime("%H:%M:%S")

    variables = {
        "$full_date_text": str_full_date,
        "$date_text": str_date,
        "$date": date,
        "$time": time_,
        "$full_time": time_full,
        "$username": order.buyer_username,
        "$order_desc": order.description if isinstance(order, FunPayAPI.types.OrderShortcut) else order.short_description if order.short_description else "",
        "$order_title": order.description if isinstance(order, FunPayAPI.types.OrderShortcut) else order.short_description if order.short_description else "",
        "$order_id": order.id
    }

    for var in variables:
        text = text.replace(var, variables[var])
    return text


def restart_program():
    """
    Полный перезапуск FPV.
    """
    python = sys.executable
    os.execl(python, python, *sys.argv)
    try:
        process = psutil.Process()
        for handler in process.open_files():
            os.close(handler.fd)
        for handler in process.connections():
            os.close(handler.fd)
    except:
        pass


def shut_down():
    """
    Полное отключение FPV.
    """
    try:
        process = psutil.Process()
        process.terminate()
    except:
        pass

from account_rental.db import get_all_rented_accounts, free_account
from datetime import datetime
import logging

logger = logging.getLogger("FPV")

def check_and_reset_rentals():
    from vertex import get_vertex
    vertex = get_vertex()
    accounts = get_all_rented_accounts()
    now = datetime.now()

    for acc in accounts:
        rent_end = acc["rent_end"]
        if isinstance(rent_end, str):
            try:
                rent_end = datetime.strptime(rent_end, "%Y-%m-%d %H:%M:%S")
            except:
                continue

        if rent_end < now:
            free_account(acc["id"])
            logger.debug(f"✅ Аккаунт {acc['login']} освобождён.")

            # Отправляем уведомление пользователю
            if vertex and vertex.account:
                try:
                    vertex.account.send_message(acc["renter"], "⏰ Ваша аренда аккаунта завершена. Благодарим за использование сервиса!")
                    logger.debug(f"📩 Уведомление отправлено пользователю {acc['renter']}.")
                except Exception as e:
                    logger.error(f"❗ Ошибка при отправке уведомления: {e}")
