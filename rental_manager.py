import sqlite3
from datetime import datetime, timedelta
import threading
import time

class RentalManager:
    def __init__(self):
        self.db = sqlite3.connect('rentals.db')
        self._init_db()
        self._start_background_check()

    def _init_db(self):
        """Создает таблицу для аренды."""
        cursor = self.db.cursor()
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS rentals (
            id INTEGER PRIMARY KEY,
            user_id TEXT,
            username TEXT,
            account_data TEXT,
            lot_name TEXT,
            end_time TEXT
        )
        ''')
        self.db.commit()

    def add_rental(self, user_id, username, account_data, lot_name, duration_hours):
        """Добавляет запись об аренде."""
        end_time = (datetime.now() + timedelta(hours=duration_hours)).strftime('%Y-%m-%d %H:%M:%S')
        cursor = self.db.cursor()
        cursor.execute('''
        INSERT INTO rentals (user_id, username, account_data, lot_name, end_time)
        VALUES (?, ?, ?, ?, ?)
        ''', (user_id, username, account_data, lot_name, end_time))
        self.db.commit()
        return f"Аккаунт {account_data} арендован до {end_time}"

    def get_active_rentals(self):
        """Возвращает список активных аренд."""
        cursor = self.db.cursor()
        cursor.execute('SELECT * FROM rentals WHERE end_time > datetime("now")')
        return cursor.fetchall()

    def _check_expired_rentals(self):
        """Фоновая проверка просроченных аренд."""
        while True:
            cursor = self.db.cursor()
            cursor.execute('DELETE FROM rentals WHERE end_time <= datetime("now")')
            self.db.commit()
            time.sleep(60)

    def _start_background_check(self):
        """Запускает фоновую проверку."""
        thread = threading.Thread(target=self._check_expired_rentals, daemon=True)
        thread.start()