import sqlite3
import os
from datetime import datetime, timedelta

DB_NAME = r"C:\Users\Rofler\Desktop\RentGame\Vertex++\account_rental\storage\accounts.db"


def get_connection():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    return conn

def create_tables():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS accounts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            login TEXT UNIQUE,
            password TEXT,
            status TEXT,  -- "free" или "rented"
            renter TEXT,
            rent_end DATETIME
        )
    ''')
    conn.commit()
    conn.close()

def add_account(login, password):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('''
        INSERT OR IGNORE INTO accounts (login, password, status)
        VALUES (?, ?, "free")
    ''', (login, password))
    conn.commit()
    conn.close()

def get_free_account():
    conn = get_connection()
    cursor = conn.cursor()
    now = datetime.now()
    cursor.execute('''
        SELECT * FROM accounts
        WHERE status = "free"
        AND (rent_end IS NULL OR rent_end < ?)
        LIMIT 1
    ''', (now,))
    account = cursor.fetchone()
    conn.close()
    return account


def rent_account(account_id, renter, rent_hours):
    conn = get_connection()
    cursor = conn.cursor()
    rent_end = datetime.now() + timedelta(hours=rent_hours)
    cursor.execute('''
        UPDATE accounts SET status = "rented", renter = ?, rent_end = ?
        WHERE id = ?
    ''', (renter, rent_end, account_id))
    conn.commit()
    conn.close()

def free_account(account_id, new_password=None):
    print(f"[DB] free_account вызвана для account_id={account_id}")
    conn = get_connection()
    cursor = conn.cursor()
    if new_password:
        cursor.execute('''
            UPDATE accounts SET status = "free", renter = NULL, rent_end = NULL, password = ?
            WHERE id = ?
        ''', (new_password, account_id))
    else:
        cursor.execute('''
            UPDATE accounts SET status = "free", renter = NULL, rent_end = NULL
            WHERE id = ?
        ''', (account_id,))
    conn.commit()
    conn.close()

def get_rented_accounts():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM accounts WHERE status = "rented"')
    accounts = cursor.fetchall()
    conn.close()
    return accounts

if __name__ == "__main__":
    from os.path import exists

    if not exists("accounts.db"):
        create_tables()
        add_account("test_login_1", "test_pass_1")
        add_account("test_login_2", "test_pass_2")
        print("✅ База создана и аккаунты добавлены.")
    else:
        print("⚠️ База уже существует.")

def get_all_rented_accounts():
    import os
    print(f"[DB] Используемая база: {os.path.abspath(DB_NAME)}")
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    cur.execute("SELECT id, login, rent_end, renter FROM accounts WHERE status = 'rented'")
    rows = cur.fetchall()
    print(f"[DB] Найдено арендованных аккаунтов: {len(rows)}")
    conn.close()

    accounts = []
    for row in rows:
        rent_end_dt = row["rent_end"]
        if isinstance(rent_end_dt, str):
            try:
                # Попытка парсинга с микросекундами
                rent_end_dt = datetime.strptime(rent_end_dt, "%Y-%m-%d %H:%M:%S.%f")
            except ValueError:
                try:
                    # Если не удалось, парсим без микросекунд
                    rent_end_dt = datetime.strptime(rent_end_dt, "%Y-%m-%d %H:%M:%S")
                except Exception as e:
                    print(f"[DB] Ошибка парсинга rent_end для аккаунта {row['login']}: {e}")
                    continue

        accounts.append({
            "id": row["id"],
            "login": row["login"],
            "rent_end": rent_end_dt,
            "renter": row["renter"]
        })

    return accounts



def release_account(account_id):
    """
    Освобождает аккаунт: сбрасывает статус, арендатора и время аренды.
    """
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        UPDATE accounts
        SET status = 'free', renter = NULL, rent_end = NULL
        WHERE id = ?
    """, (account_id,))

    conn.commit()
    conn.close()