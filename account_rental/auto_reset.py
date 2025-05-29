import threading
import time
from datetime import datetime
from .db import get_rented_accounts, free_account

def reset_expired_accounts_loop(interval_seconds=60):
    def loop():
        while True:
            try:
                rented = get_rented_accounts()
                count = 0
                now = datetime.now()

                for acc in rented:
                    if acc["rent_end"] and datetime.strptime(acc["rent_end"], "%Y-%m-%d %H:%M:%S") < now:
                        free_account(acc["id"])
                        count += 1

                if count > 0:
                    print(f"[AUTO RESET] Сброшено аккаунтов: {count}")
            except Exception as e:
                print(f"[AUTO RESET] Ошибка: {e}")

            time.sleep(interval_seconds)

    threading.Thread(target=loop, daemon=True).start()
