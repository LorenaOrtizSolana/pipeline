import csv
import datetime
import random
from datetime import timedelta
from dateutil import parser
import pytz

random.seed(42)

TIMEZONES = ["Europe/Berlin", "America/New_York", "Europe/London"]


def random_timezone():
    return pytz.timezone(random.choices(TIMEZONES, weights=[0.8, 0.1, 0.1])[0])


def generate_date(start_date, end_date, tz_selected):
    delta = end_date - start_date
    delta_in_second = delta.days * 24 * 3600 + delta.seconds
    random_second = random.randrange(delta_in_second)
    date = start_date + timedelta(seconds=random_second)
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


def generate_account(num_accounts=50):
    dtst_acc = [['AccountID', 'Status', 'Currency', 'OpeningDate', 'AccountTypeCode', 'Timezone']]
    for i in range(num_accounts):
        types_choice = random.choice(['CACC', 'SAVG', 'LOAN'])
        tz_selected = random_timezone()
        tz_name = tz_selected.zone

        date_future_choice = random.choices([1, 2], weights=[0.9, 0.1])[0]
        if date_future_choice == 2:
            start_date = datetime.datetime(2026, 12, 12)
            end_date = datetime.datetime(2027, 12, 12)
        else:
            start_date = datetime.datetime(2024, 1, 1)
            end_date = datetime.datetime.now()
        opening_date = generate_date(start_date, end_date, tz_selected)
        status_choice = random.choices(['ACTIVE', 'CLOSED'], weights=[0.85, 0.15])[0]
        dtst_acc.append([i, status_choice, generate_currency(), opening_date.isoformat(), types_choice, tz_name])
    return dtst_acc


def generate_transactions(dtst, min_txn=1, max_txn=5):
    dtst_txn = [['TransactionID', 'AccountID', 'Date', 'Amount', 'Debit/Credit', 'Status', 'Timezone']]
    currency_list = ["USD", "EUR", "SEK"]
    txn_id = 0
    for row in dtst[1:]:
        account_id = row[0]
        col_curr = row[2]
        col_date_str = row[3]
        try:
            tz_name = row[5] if len(row) > 5 and row[5] else random_timezone().zone
            tz_selected = pytz.timezone(tz_name)
        except Exception:
            tz_selected = random_timezone()
        if not col_date_str:
            col_date = generate_date(datetime.datetime(2024, 1, 1), datetime.datetime(2025, 12, 12), tz_selected)
        else:
            try:
                col_date = parser.parse(col_date_str)
            except Exception:
                col_date = generate_date(datetime.datetime(2024, 1, 1), datetime.datetime(2025, 12, 12), tz_selected)
            if col_date.tzinfo is None:
                col_date = tz_selected.localize(col_date)
        num_txn = random.randint(min_txn, max_txn)
        for _ in range(num_txn):
            txn_id += 1
            txn_tz_selected = random_timezone()
            txn_tz_name = txn_tz_selected.zone
            txn_start_date = datetime.datetime(2023, 1, 1)
            txn_end_date = datetime.datetime(2025, 12, 12)
            txn_start_date = txn_tz_selected.localize(txn_start_date)
            txn_end_date = txn_tz_selected.localize(txn_end_date)
            if col_curr == 'USD':
                curr_choice = random.choices(currency_list, weights=[0.8, 0.1, 0.1])[0]
            elif col_curr == 'EUR':
                curr_choice = random.choices(currency_list, weights=[0.1, 0.8, 0.1])[0]
            else:  # SEK
                curr_choice = random.choices(currency_list, weights=[0.1, 0.1, 0.8])[0]
            txndate_inpast = random.choices([0, 1], weights=[0.9, 0.1])[0]
            if txndate_inpast == 1:
                delta = col_date - txn_start_date
                delta_seconds = delta.days * 86400 + delta.seconds
                random_second = random.randrange(delta_seconds) if delta_seconds > 0 else 0
                date = txn_start_date + timedelta(seconds=random_second)
            else:
                delta = txn_end_date - col_date
                delta_seconds = delta.days * 86400 + delta.seconds
                random_second = random.randrange(delta_seconds) if delta_seconds > 0 else 0
                date = col_date + timedelta(seconds=random_second)
                if date.tzinfo is None:
                    date = txn_tz_selected.localize(date)
                else:
                    date = date.astimezone(txn_tz_selected)
            debcred_choice = random.choice(["DEBIT", "CREDIT"])
            amount = generate_amount()
            amount = abs(amount) if debcred_choice == "DEBIT" else -abs(amount)
            dtst_txn.append([
                txn_id,
                account_id,
                date.isoformat(),
                amount,
                debcred_choice,
                generate_statustxn(),
                txn_tz_name
            ])
    return dtst_txn


def add_row_duplicates(table, num_duplicates=1, percent_duplicates=0.05):
    header = table[0]
    rows = table[1:]
    n = len(rows)
    total_duplicates = max(num_duplicates, int(n * percent_duplicates))
    indices = random.choices(range(n), k=total_duplicates)
    duplicates = [rows[i] for i in indices]
    random.shuffle(duplicates)
    new_rows = rows + duplicates
    random.shuffle(new_rows)
    return [header] + new_rows


def add_partial_nulls(table, percent_nulls=0.05, min_fields=1, max_fields=5, exclude_cols=None):
    header = table[0]
    rows = table[1:]
    n = len(rows)
    num_null_rows = int(n * percent_nulls)
    indices = random.sample(range(n), num_null_rows)
    if max_fields is None:
        max_fields = len(header) - 1
    if exclude_cols is None:
        exclude_cols = [0]
    for idx in indices:
        possible_fields = [i for i in range(len(header)) if i not in exclude_cols]
        num_fields_to_null = random.randint(min_fields, min(max_fields, len(possible_fields)))
        fields_to_null = random.sample(possible_fields, num_fields_to_null)
        for f in fields_to_null:
            rows[idx][f] = ""
    return [header] + rows


def randomize_date_formats(table, date_col_idx, percent_change=0.1, exclude_header=True):
    date_formats = [
        "%Y-%m-%dT%H:%M:%S%z",
        "%Y-%m-%d %H:%M:%S",
        "%d/%m/%Y %H:%M",
        "%m-%d-%Y %I:%M %p",
        "%Y/%m/%d",
        "%d-%b-%Y",
        "%Y-%m-%d",
    ]
    header = table[0] if exclude_header else []
    rows = table[1:] if exclude_header else table
    n = len(rows)
    num_to_change = int(n * percent_change)
    indices = random.sample(range(n), num_to_change)
    for idx in indices:
        row = rows[idx]
        date_str = row[date_col_idx]
        if not date_str:
            continue
        try:
            dt = parser.parse(date_str)
            fmt = random.choice(date_formats)

            if "%z" not in fmt and dt.tzinfo is not None:
                dt = dt.astimezone(datetime.timezone.utc).replace(tzinfo=None)
            new_date_str = dt.strftime(fmt)
            row[date_col_idx] = new_date_str
        except Exception:
            continue
    return [header] + rows if exclude_header else rows


def add_field_errors(table, percent_error=0.03, error_fields=None):
    header = table[0]
    rows = table[1:]
    n = len(rows)
    num_error_rows = int(n * percent_error)
    indices = random.sample(range(n), num_error_rows)
    if error_fields is None:
        error_fields = list(range(len(header)))

    typo_map = {
        "BOOK": "BOK", "ACTIVE": "ACTVE", "CLOSED": "CLOSE", "PENDING": "PENDNG", "REJECTED": "REJCTD",
        "USD": "US", "EUR": "EURO", "SEK": "SEKK", "DEBIT": "debit", "CREDIT": "CREIT",
        "CACC": "CACCX", "SAVG": "SAV", "LOAN": "LOA"
    }
    nonsense = ["???", "N/A", "null", "xxxx"]

    for idx in indices:
        row = rows[idx]
        for col in error_fields:
            val = row[col]
            if not val:
                continue

            err_type = random.choice(["typo", "nonsense", "case", "whitespace"])
            if err_type == "typo" and str(val) in typo_map:
                row[col] = typo_map[str(val)]
            elif err_type == "nonsense":
                row[col] = random.choice(nonsense)
            elif err_type == "case":
                row[col] = str(val).lower() if random.random() < 0.5 else str(val).upper()
            elif err_type == "whitespace":
                row[col] = f"  {val}  "
    return [header] + rows


if __name__ == '__main__':
    accounts = generate_account(num_accounts=150)
    accounts_with_dupes = add_row_duplicates(accounts, percent_duplicates=0.05)
    accounts_with_nulls = add_partial_nulls(accounts_with_dupes, percent_nulls=0.05, min_fields=1, max_fields=4,
                                            exclude_cols=[0])
    accounts_with_mixed_dates = randomize_date_formats(accounts_with_nulls, date_col_idx=3, percent_change=0.15)
    accounts_with_errors = add_field_errors(accounts_with_mixed_dates, percent_error=0.09, error_fields=[1, 2])

    transactions = generate_transactions(accounts_with_mixed_dates, min_txn=1, max_txn=3)
    transactions_with_dupes = add_row_duplicates(transactions, percent_duplicates=0.1)
    transactions_with_nulls = add_partial_nulls(transactions_with_dupes, percent_nulls=0.05, min_fields=1, max_fields=5,
                                                exclude_cols=[0, 1])
    transactions_with_mixed_dates = randomize_date_formats(transactions_with_nulls, date_col_idx=2, percent_change=0.15)
    transactions_with_errors = add_field_errors(transactions_with_mixed_dates, percent_error=0.09,
                                                error_fields=[4, 5, 6])

    with open('accounts.csv', 'w', newline='') as acc_csv:
        writer = csv.writer(acc_csv)
        writer.writerows(accounts_with_errors)

    with open('transactions.csv', 'w', newline='') as txn_csv:
        writer = csv.writer(txn_csv)
        writer.writerows(transactions_with_errors)