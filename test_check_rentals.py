from account_rental.db import get_all_rented_accounts

accounts = get_all_rented_accounts()
print(f"Найдено арендованных аккаунтов: {len(accounts)}")
for acc in accounts:
    print(acc)
