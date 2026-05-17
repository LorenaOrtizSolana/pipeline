import csv
import datetime
import random
from datetime import timedelta
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
    return date


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


def generate_transactions():
    dtst = [['Date', 'Amount', 'Currency', 'Debit/Credit', 'Status']]
    start_date = datetime.datetime(2025, 1, 1)
    end_date = datetime.datetime(2026, 2, 2)

    for i in range(3):
        debcred_choice = random.choice(["DEBIT", "CREDIT"])
        amount = generate_amount()
        amount = abs(amount) if debcred_choice == "DEBIT" else -abs(amount)

        dtst.append([
            generate_date(start_date, end_date),
            amount,
            generate_currency(),
            debcred_choice,
            generate_statustxn()
        ])
    return dtst


def generate_account(dtst):
    dtst_acc = [['Status', 'Currency', 'OpeningDate', 'AccountTypeCode']]
    col_curr = [row[2] for row in dtst[1:]]
    col_date = [row[0] for row in dtst[1:]]

    start_date = datetime.datetime(2024, 1, 1)
    end_date = datetime.datetime(2026, 12, 12)

    for i in range(3):
        types_choice = random.choice(['CACC', 'SAVG', 'LOAN'])

        currency_list = ["USD", "EUR", "SEK"]
        if col_curr[i] == 'USD':
            curr_choice = random.choices(currency_list, weights=[0.8, 0.1, 0.1])[0]
        elif col_curr[i] == 'EUR':
            curr_choice = random.choices(currency_list, weights=[0.1, 0.8, 0.1])[0]
        else:  # SEK
            curr_choice = random.choices(currency_list, weights=[0.1, 0.1, 0.8])[0]

        datefuture = random.choices([0, 1], weights=[0.9, 0.1])[0]

        if datefuture == 1:
            delta = end_date - col_date[i]
            delta_seconds = delta.days * 86400 + delta.seconds
            random_second = random.randrange(delta_seconds) if delta_seconds > 0 else 0
            date = col_date[i] + timedelta(seconds=random_second)
        else:
            delta = col_date[i] - start_date
            delta_seconds = delta.days * 86400 + delta.seconds
            random_second = random.randrange(delta_seconds) if delta_seconds > 0 else 0
            date = start_date + timedelta(seconds=random_second)

        dtst_acc.append([generate_statustxn(), curr_choice, date, types_choice])
    return dtst_acc


if __name__ == '__main__':
    with open('transaction_records.csv', 'w', newline='') as txn_csv:
        writer = csv.writer(txn_csv)
        writer.writerows(generate_transactions())
    transactions = generate_transactions()
    with open('accounts.csv', 'w', newline='') as acc_csv:
         writer = csv.writer(acc_csv)
         writer.writerows(generate_account(transactions))