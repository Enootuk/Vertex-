from account_rental.db import get_connection
from datetime import datetime

def reset_expired_accounts():
    conn = get_connection()
    cursor = conn.cursor()
    now = datetime.now()

    cursor.execute('''
        UPDATE accounts
        SET status = "free", renter = NULL, rent_end = NULL
        WHERE status = "rented" AND rent_end IS NOT NULL AND rent_end < ?
    ''', (now,))
    affected = cursor.rowcount
    conn.commit()
    conn.close()

    print(f"✅ Сброшено аккаунтов: {affected}")

if __name__ == "__main__":
    reset_expired_accounts()
