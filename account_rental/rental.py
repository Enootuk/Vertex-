from .db import get_free_account, rent_account
from datetime import datetime
from datetime import timedelta


def issue_account(renter_id, rent_hours):
    account = get_free_account()
    if not account:
        return None  # Нет свободных аккаунтов
    rent_account(account['id'], renter_id, rent_hours)
    rent_end = datetime.now() + timedelta(hours=rent_hours)
    return {
        'login': account['login'],
        'password': account['password'],
        'rent_end': rent_end.strftime('%Y-%m-%d %H:%M:%S')
    }

if __name__ == "__main__":
    from pprint import pprint
    result = issue_account("test_user", 1)
    pprint(result)

