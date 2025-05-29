import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(__file__), "accounts.db")

conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()

try:
    cursor.execute("ALTER TABLE accounts ADD COLUMN renter TEXT")
    print("✅ Столбец 'renter' добавлен.")
except sqlite3.OperationalError as e:
    if "duplicate column name" in str(e):
        print("ℹ️ Столбец 'renter' уже существует.")
    else:
        raise

conn.commit()
conn.close()
