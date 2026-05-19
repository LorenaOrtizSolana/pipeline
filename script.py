import csv
import datetime
import random
from datetime import timedelta, timezone
import pytz

random.seed(42)


def generate_date(start_date, end_date):
    delta = end_date - start_date
    delta_in_second = delta.days * 24 * 3600 + delta.seconds
    random_second = random.randrange(delta_in_second)
    date = start_date + timedelta(seconds=random_second)

    timezones = ["Europe/Berlin", "America/New_York", "Europe/London"]
    time_choice = random.choices(timezones, weights=[0.8, 0.1, 0.1])[0]
    tz_selected = pytz.timezone(time_choice)
    date = tz_selected.localize(date)
    date_utc = date.astimezone(pytz.utc)
    return date_utc


def generate_amount():
    intervals = [1, 2, 3, 4]
    inter_choice = random.choices(intervals, weights=[0.1, 0.2, 0.6, 0.1])[0]
    if inter_choice == 1:
        amount = random.randint(100, 199)
    elif inter_choice == 2:
        amount = random.randint(200, 599)
    elif inter_choice == 3:
        amount = random.randint(600, 1999)
    else:
        amount = random.randint(2000, 2500)
    return amount


def generate_currency():
    currency_list = ["USD", "EUR", "SEK"]
    curr_choice = random.choices(currency_list, weights=[0.1, 0.8, 0.1])[0]
    return curr_choice


def generate_statustxn():
    status_list = ["BOOK", "PENDING", "REJECTED"]
    status_choice = random.choice(status_list)
    return status_choice


def generate_account(num_accounts=3):
    dtst_acc = [['AccountID', 'Status', 'Currency', 'OpeningDate', 'AccountTypeCode']]
    for i in range(num_accounts):
        types_choice = random.choice(['CACC', 'SAVG', 'LOAN'])
        start_date = datetime.datetime(2024, 1, 1)
        end_date = datetime.datetime(2026, 12, 12)
        opening_date = generate_date(start_date, end_date)
        dtst_acc.append([i, generate_statustxn(), generate_currency(), opening_date.isoformat(), types_choice])
    return dtst_acc


def generate_transactions(dtst):
    dtst_txn = [['Date', 'Amount', 'Currency', 'Debit/Credit', 'Status']]
    currency_list = ["USD", "EUR", "SEK"]
    start_date = datetime.datetime(2024, 1, 1, tzinfo=timezone.utc)
    end_date = datetime.datetime(2026, 12, 12, tzinfo=timezone.utc)
    col_curr = [row[2] for row in dtst[1:]]
    col_date = [datetime.datetime.fromisoformat(row[3]) for row in dtst[1:]]

    for i in range(len(col_curr)):
        if col_curr[i] == 'USD':
            curr_choice = random.choices(currency_list, weights=[0.8, 0.1, 0.1])[0]
        elif col_curr[i] == 'EUR':
            curr_choice = random.choices(currency_list, weights=[0.1, 0.8, 0.1])[0]
        else:  # SEK
            curr_choice = random.choices(currency_list, weights=[0.1, 0.1, 0.8])[0]

        txndate_inpast = random.choices([0, 1], weights=[0.9, 0.1])[0]
        if txndate_inpast == 1:
            delta = col_date[i] - start_date
            delta_seconds = delta.days * 86400 + delta.seconds
            random_second = random.randrange(delta_seconds) if delta_seconds > 0 else 0
            date = start_date + timedelta(seconds=random_second)
        else:
            delta = end_date - col_date[i]
            delta_seconds = delta.days * 86400 + delta.seconds
            random_second = random.randrange(delta_seconds) if delta_seconds > 0 else 0
            date = col_date[i] + timedelta(seconds=random_second)

        date = date.replace(tzinfo=timezone.utc)

        debcred_choice = random.choice(["DEBIT", "CREDIT"])
        amount = generate_amount()
        amount = abs(amount) if debcred_choice == "DEBIT" else -abs(amount)

        dtst_txn.append([
            date.isoformat(),
            amount,
            curr_choice,
            debcred_choice,
            generate_statustxn()
        ])
    return dtst_txn


if __name__ == '__main__':
    accounts = generate_account(num_accounts=3)

    with open('accounts.csv', 'w', newline='') as acc_csv:
        writer = csv.writer(acc_csv)
        writer.writerows(accounts)

    with open('transaction_records.csv', 'w', newline='') as txn_csv:
        writer = csv.writer(txn_csv)
        writer.writerows(generate_transactions(accounts))