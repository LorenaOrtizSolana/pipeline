import sqlite3
import csv
import itertools

conn = sqlite3.connect('test_db.db')
cursor = conn.cursor()

cursor.execute('''
               CREATE TABLE IF NOT EXISTS accounts
               (
                   AccountId
                   INTEGER
                   PRIMARY
                   KEY
                   AUTOINCREMENT,
                   Status
                   VARCHAR
               (
                   255
               ),
                   Currency INTEGER,
                   OpeningDate DATETIME,
                   AccountTypeCode CHAR
               (
                   10
               ),
                   Timezone VARCHAR
               (
                   255
               )
                   )
               ''')

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

cursor.execute('''
               CREATE TABLE IF NOT EXISTS transactions
               (
                   TransactionId
                   INTEGER
                   PRIMARY
                   KEY
                   AUTOINCREMENT,
                   AccountId
                   INTEGER,
                   Date
                   DATETIME,
                   Amount
                   REAL,
                   Currency
                   INTEGER,
                   DebitCredit
                   TEXT,
                   Status
                   TEXT,
                   Timezone
                   TEXT,
                   FOREIGN
                   KEY
               (
                   AccountId
               ) REFERENCES accounts
               (
                   AccountId
               )
                   )
               ''')

cursor.execute('DELETE FROM transactions')
cursor.execute('DELETE FROM sqlite_sequence WHERE name="transactions"')
with open('transactions.csv', newline='', encoding='utf-8') as csvfile:
    reader = csv.reader(csvfile)
    next(reader)
    for row in reader:
        cursor.execute('''
                       INSERT INTO transactions (AccountId, Date, Amount, Currency, DebitCredit, Status, Timezone)
                       VALUES (?, ?, ?, ?, ?, ?, ?)
                       ''', row[1:])
"""
# Print accounts   
print("Accounts:")   
cursor.execute('SELECT * FROM accounts')   
for row in cursor.fetchall():   
    print(row)   
"""
"""
# Print transactions   
print("\nTransactions:")   
cursor.execute('SELECT * FROM transactions')   
for row in cursor.fetchall():   
    print(row)   
"""
"""
cursor.execute('SELECT AccountId, TransactionId FROM transactions')
rows = cursor.fetchall()
rows_todict = dict(rows)
print(rows_todict)
"""

cursor.execute('SELECT TransactionId,AccountId FROM transactions')
rows = cursor.fetchall()
map_ids = dict(rows)

flipped_map_ids = {}

for key, value in map_ids.items():
    if value not in flipped_map_ids:
        flipped_map_ids[value] = [key]
    else:
        flipped_map_ids[value].append(key)
# print(flipped_map_ids)

cursor.execute('SELECT COUNT(TransactionId) from transactions')
res1 = cursor.fetchall()
res1 = list(itertools.chain(*res1))[0]

cursor.execute('SELECT COUNT(DISTINCT DATE) AS NumUnDates from transactions')
res2 = cursor.fetchall()
res2 = list(itertools.chain(*res2))[0]
print(f"{res1} transactions, from which {res1 - res2} have duplicate dates.")

cursor.execute('SELECT DISTINCT DATE AS NumUnDates from transactions')
res_disdates = cursor.fetchall()
list_uniquedates = []
for row in res_disdates:
    list_uniquedates.append(row[0])

dict_dates = {}
for unique_date in list_uniquedates:
    cursor.execute('SELECT TransactionId, AccountId, Date FROM transactions WHERE Date = ?', (unique_date,))
    rows = cursor.fetchall()
    dict_dates[unique_date] = rows


# print(dict_dates)
def keys_with_multiple_values(d):
    result = []
    for key, value in d.items():
        if isinstance(value, list) and len(value) > 1:
            result.append(key)
    return result


keys = keys_with_multiple_values(dict_dates)
num_dupdates = len(keys)
print(f"{num_dupdates} dates are duplicated and {res1 - res2 - num_dupdates} other are empty")

for key in keys:
    transaction_idlist = dict_dates.get(key)
    for transaction_id in transaction_idlist:
        transaction_id = transaction_id[0]
        cursor.execute('SELECT TransactionId, AccountId, Date FROM transactions WHERE TransactionId= ?',
                       (transaction_id,))
        rows = cursor.fetchall()
        print(rows)

conn.commit()
conn.close()