import time
from datetime import datetime
from db import get_rented_accounts, free_account
from telegram import Bot

TOKEN = 'ТВОЙ_ТОКЕН_ТЕЛЕГРАМ_БОТА'
bot = Bot(token=TOKEN)

def change_steam_password(account_login):
    # Здесь ты можешь добавить логику смены пароля через Steam API или вручную
    # Пока заглушка
    new_password = 'new_password123'
    return new_password

def notify_user(chat_id, message):
    bot.send_message(chat_id=chat_id, text=message)

def check_expired_rentals():
    while True:
        accounts = get_rented_accounts()
        now = datetime.now()
        for acc in accounts:
            try:
                rent_end = datetime.strptime(rent_end, "%Y-%m-%d %H:%M:%S.%f")
            except ValueError:
                rent_end = datetime.strptime(rent_end, "%Y-%m-%d %H:%M:%S")
            if now >= rent_end:
                # Меняем пароль
                new_pass = change_steam_password(acc['login'])
                free_account(acc['id'], new_pass)
                notify_user(acc['renter'], f'Аренда аккаунта {acc["login"]} завершена. Пароль был изменён.')
        time.sleep(60)  # Проверяем каждую минуту

if __name__ == '__main__':
    check_expired_rentals()
