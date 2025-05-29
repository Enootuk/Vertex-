import sqlite3
import os

# Путь к базе — проверьте, соответствует ли он тому, который использует issue_account()
DB_PATH = os.path.join(os.path.dirname(__file__), "account_rental" , "storage", "accounts.db")


os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()

# Создаём таблицу accounts, если её нет
cursor.execute("""
CREATE TABLE IF NOT EXISTS accounts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    login TEXT NOT NULL,
    password TEXT NOT NULL,
    rent_end TEXT,
    renter TEXT,
    status TEXT DEFAULT 'free'
);
""")



conn.commit()
conn.close()
print(f"✅ База и таблица accounts созданы или уже существуют в {DB_PATH}")
