import sqlite3
import csv
import re
from pathlib import Path

BASE = Path(__file__).resolve().parent
DATA_DIR = BASE.parent / "data"
DB_PATH = BASE / "berka_db.db"

conn = sqlite3.connect(DB_PATH)
conn.execute('PRAGMA foreign_keys = ON')
cursor = conn.cursor()

## account
accounts_create = '''
CREATE TABLE IF NOT EXISTS accounts (
    AccountId INTEGER PRIMARY KEY,
    DistrictId INTEGER NOT NULL,
    Frequency VARCHAR(255),
    Date DATETIME
)
'''

## trans
txns_create = '''
CREATE TABLE IF NOT EXISTS txns (
    TransId INTEGER PRIMARY KEY,
    AccountId INTEGER NOT NULL,
    Date DATETIME,
    Type VARCHAR(255),
    Operation VARCHAR(255),
    Amount INTEGER NOT NULL,
    Balance INTEGER NOT NULL,
    K_symbol VARCHAR(255),
    Bank VARCHAR(255),
    Account INTEGER NOT NULL
)
'''

## order
orders_create = '''
CREATE TABLE IF NOT EXISTS orders (
    OrderId INTEGER PRIMARY KEY,
    AccountId INTEGER NOT NULL,
    Bank_to CHAR(10),
    Account_to INTEGER NOT NULL,
    Amount INTEGER NOT NULL,
    K_symbol VARCHAR(255)
)
'''

## loan
loans_create = '''
CREATE TABLE IF NOT EXISTS loans (
    LoanId INTEGER PRIMARY KEY,
    AccountId INTEGER NOT NULL,
    Date DATETIME,
    Amount INTEGER NOT NULL,
    Duration INTEGER NOT NULL,
    Payments INTEGER NOT NULL,
    Status CHAR(10)
)
'''

## district
districts_create = '''
CREATE TABLE IF NOT EXISTS districts (
    DistrictId INTEGER PRIMARY KEY,
    DistrictName VARCHAR(255),
    Region VARCHAR(255),
    NumInhabitants INTEGER NOT NULL,
    NumMunicipalities_Under_499Inhabitants INTEGER NOT NULL,
    NumMunicipalities_500_1999Inhabitants INTEGER NOT NULL,
    NumMunicipalities_2000_9999Inhabitants INTEGER NOT NULL,
    NumMunicipalities_Over_10000Inhabitants INTEGER NOT NULL,
    NumCities INTEGER NOT NULL,
    RatioOfUrbanInhabitants DECIMAL(4,1),
    AverageSalary INTEGER NOT NULL,
    UnemploymentRate1995 DECIMAL(5,2),
    UnemploymentRate1996 DECIMAL(5,2),
    NumEnterpreneurs_Per_1000_Inhabitants INTEGER NOT NULL,
    NumCrimesCommited_In_1995 INTEGER NOT NULL,
    NumCrimesCommited_In_1996 INTEGER NOT NULL
)
'''

## card
cards_create = '''
CREATE TABLE IF NOT EXISTS cards (
    CardId INTEGER PRIMARY KEY,
    DispId INTEGER NOT NULL,
    Type VARCHAR(255),
    Issued DATETIME
)
'''

## client
clients_create = '''
CREATE TABLE IF NOT EXISTS clients (
    ClientId INTEGER PRIMARY KEY,
    BirthNum INTEGER NOT NULL,
    DistrictId INTEGER NOT NULL
)
'''

## disp
disps_create = '''
CREATE TABLE IF NOT EXISTS disps (
    DispId INTEGER PRIMARY KEY,
    ClientId INTEGER NOT NULL,
    AccountId INTEGER NOT NULL,
    Type VARCHAR(255)
)
'''

files_and_tables = [
    ("account.csv",  'accounts'),
    ("trans.csv",    'txns'),
    ("order.csv",    'orders'),
    ("loan.csv",     'loans'),
    ("district.csv", 'districts'),
    ("card.csv",     'cards'),
    ("client.csv",   'clients'),
    ("disp.csv",     'disps'),
]

create_sqls = {
    'accounts':  accounts_create,
    'txns':      txns_create,
    'orders':    orders_create,
    'loans':     loans_create,
    'districts': districts_create,
    'cards':     cards_create,
    'clients':   clients_create,
    'disps':     disps_create,
}


def does_col_have_nulls(csv_path, delimiter=';'):
    dict_empties = {}

    with open(csv_path, newline='', encoding='utf-8') as f:
        reader = csv.reader(f, delimiter=delimiter)
        header = next(reader, None)
        num_cols = len(header)

        for i in range(num_cols):
            dict_empties[i] = False

        while False in list(dict_empties.values()):
            try:
                row = next(reader)
                if not row:
                    continue
                new_values = [(row[i].strip() == '' or row[i].strip().upper() == 'NULL') for i in range(num_cols)]

                for i, (k, v) in enumerate(dict_empties.items()):
                    if new_values[i]:
                        dict_empties[k] = new_values[i]

            except StopIteration:
                break

    return dict_empties


for csv_name, table_name in files_and_tables:
    csv_path = DATA_DIR / csv_name
    result = does_col_have_nulls(csv_path)

    with open(csv_path, newline='', encoding='utf-8') as f:
        header = next(csv.reader(f, delimiter=';'))

    cols_to_relax = [header[i] for i, has_nulls in result.items() if has_nulls]

    sql = create_sqls[table_name]
    for col in cols_to_relax:
        sql = re.sub(
            rf'(\b{col}\b\s+\S+(?:\(\d+(?:,\d+)?\))?)\s+NOT NULL',
            r'\1',
            sql,
            flags=re.IGNORECASE,
        )

    cursor.execute(f'DROP TABLE IF EXISTS {table_name}')
    cursor.execute(sql)

    create_sqls[table_name] = sql


def extract_new_column_names(query_create, skip_pk=False):
    after_whitespace = re.findall(r'^\s+(?![A-Z]{2,})(\w+)\s', query_create, re.MULTILINE)
    return after_whitespace[1:] if skip_pk else after_whitespace


def extract_old_column_names(csv_path, skip_pk=False, delimiter=';'):
    with open(csv_path, newline='', encoding='utf-8') as f:
        header = next(csv.reader(f, delimiter=delimiter), None)
    return header[1:] if skip_pk else header


def create_mapping(old_columns, new_columns):
    return dict(zip(old_columns, new_columns))


def load_table(csv_path, table_name, column_map, delimiter=';', skip_header=False):
    cursor.execute(f'DELETE FROM {table_name}')
    try:
        cursor.execute(f'DELETE FROM sqlite_sequence WHERE name="{table_name}"')
    except sqlite3.OperationalError:
        pass

    with open(csv_path, newline='', encoding='utf-8') as f:
        reader = csv.reader(f, delimiter=delimiter)

        if skip_header:
            next(reader, None)

        rows = []
        for row in reader:
            if not row:
                continue
            row = [None if (v.strip() == '' or v.strip() == 'NULL')
                   else v.strip() for v in row]
            rows.append(row)

    sql_cols = list(column_map.values())
    placeholders = ','.join(['?'] * len(sql_cols))
    sql = f"INSERT INTO {table_name} ({','.join(sql_cols)}) VALUES ({placeholders})"
    cursor.executemany(sql, rows)
    conn.commit()
    print(f"{table_name}: {len(rows)} rows")


for csv_name, table_name in files_and_tables:
    csv_path = DATA_DIR / csv_name
    new_cols = extract_new_column_names(create_sqls[table_name])
    old_cols = extract_old_column_names(csv_path, skip_pk=False)
    load_table(csv_path, table_name, create_mapping(old_cols, new_cols), skip_header=True)

orphan_checks = [
    "SELECT COUNT(*) FROM txns     WHERE AccountId  NOT IN (SELECT AccountId  FROM accounts)",
    "SELECT COUNT(*) FROM disps    WHERE AccountId  NOT IN (SELECT AccountId  FROM accounts)",
    "SELECT COUNT(*) FROM disps    WHERE ClientId   NOT IN (SELECT ClientId   FROM clients)",
    "SELECT COUNT(*) FROM cards    WHERE DispId     NOT IN (SELECT DispId     FROM disps)",
    "SELECT COUNT(*) FROM loans    WHERE AccountId  NOT IN (SELECT AccountId  FROM accounts)",
    "SELECT COUNT(*) FROM orders   WHERE AccountId  NOT IN (SELECT AccountId  FROM accounts)",
    "SELECT COUNT(*) FROM accounts WHERE DistrictId NOT IN (SELECT DistrictId FROM districts)",
    "SELECT COUNT(*) FROM clients  WHERE DistrictId NOT IN (SELECT DistrictId FROM districts)",
]

for q in orphan_checks:
    cursor.execute(q)
    print(q, "->", cursor.fetchone()[0])

conn.close()