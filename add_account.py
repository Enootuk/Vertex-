import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(__file__), "account_rental" , "storage", "accounts.db")
conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()

cursor.execute("""
INSERT INTO accounts (login, password, status)
VALUES (?, ?, ?)
""", ("test_login", "test_password", "free"))

conn.commit()
conn.close()
print("✅ Добавлен аккаунт test_login / test_password со статусом free")
