import sqlite3
import csv
import itertools
from datetime import datetime
from dateutil import parser

conn = sqlite3.connect('test_db.db')
conn.execute("PRAGMA foreign_keys = ON")
cursor = conn.cursor()

#### Accounts table
cursor.execute('''   
CREATE TABLE IF NOT EXISTS accounts (   
    AccountId INTEGER PRIMARY KEY AUTOINCREMENT,   
    Status VARCHAR(255),   
    Currency CHAR(10),   
    OpeningDate DATETIME,   
    AccountTypeCode CHAR(10),   
    Timezone VARCHAR(255)   
)   
''')

#### Fill accounts table
#cursor.execute('DELETE FROM transactions')
cursor.execute('DELETE FROM accounts')
cursor.execute('DELETE FROM sqlite_sequence WHERE name="accounts"')

with open('accounts.csv', newline='', encoding='utf-8') as csvfile:
    reader = csv.reader(csvfile)
    next(reader)
    for row in reader:
        cursor.execute('''   
            INSERT INTO accounts (Status, Currency, OpeningDate, AccountTypeCode, Timezone)  
            VALUES (?, ?, ?, ?, ?)   
        ''', row[1:])

#### Untouched Accounts table
cursor.execute('CREATE TABLE IF NOT EXISTS orig_accounts AS SELECT * FROM accounts')

#### Transactions table
cursor.execute('''   
CREATE TABLE IF NOT EXISTS transactions (   
    TransactionId INTEGER PRIMARY KEY AUTOINCREMENT,  
    AccountId INTEGER NOT NULL, 
    Date DATETIME,     
    Amount INTEGER,     
    DebitCredit TEXT,   
    Status TEXT,   
    Timezone TEXT, 
    FOREIGN KEY (AccountId) REFERENCES accounts(AccountId) 
        ON DELETE CASCADE 
        ON UPDATE CASCADE
)   
''')

#### Fill transactions table
cursor.execute('DELETE FROM transactions')
cursor.execute('DELETE FROM sqlite_sequence WHERE name="transactions"')

with open('transactions.csv', newline='', encoding='utf-8') as csvfile:
    reader = csv.reader(csvfile)
    next(reader)
    list_empty_accid = []
    for row in reader:
        try:
            cursor.execute(''' 
                INSERT INTO transactions (AccountId, Date, Amount, DebitCredit, Status, Timezone) 
                VALUES (?, ?, ?, ?, ?, ?) 
            ''', row[1:])
        except sqlite3.IntegrityError as e:
            if len(row) > 1:
                if row[1] == "":
                    row[1] = None
                    list_empty_accid.append(row)
            else:
                list_empty_accid.append(row)

#### Untouched Transactions table
cursor.execute('CREATE TABLE IF NOT EXISTS orig_transactions AS SELECT * FROM transactions')

#### Map TransactionIds to AccountIds
cursor.execute('SELECT TransactionId, AccountId FROM transactions')
rows0 = cursor.fetchall()
map_ids = dict(rows0)

flipped_map_ids = {}

for key, value in map_ids.items():
    if value not in flipped_map_ids:
        flipped_map_ids[value] = [key]
    else:
        flipped_map_ids[value].append(key)
# print(flipped_map_ids)

conn.commit()
conn.close()