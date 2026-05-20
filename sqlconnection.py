import sqlite3

import csv

import itertools

conn = sqlite3.connect('test_db.db')

conn.execute("PRAGMA foreign_keys = ON")

cursor = conn.cursor()

#### Accounts table

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

####

####

####


#### Fill accounts table

cursor.execute('DELETE FROM transactions')

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

    ####

####

####


#### Untouched Accounts table

cursor.execute('CREATE TABLE IF NOT EXISTS orig_accounts AS SELECT * FROM accounts')

####

####

####


####  Transactions table

cursor.execute('''

               CREATE TABLE IF NOT EXISTS transactions
               (

                   TransactionId
                   INTEGER
                   PRIMARY
                   KEY
                   AUTOINCREMENT,

                   AccountId
                   INTEGER
                   NOT
                   NULL,

                   Date
                   DATETIME,

                   Amount
                   INTEGER,

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

                           INSERT INTO transactions (AccountId, Date, Amount, Currency, DebitCredit, Status, Timezone)

                           VALUES (?, ?, ?, ?, ?, ?, ?)

                           ''', row[1:])

        except sqlite3.IntegrityError as e:

            if len(row) > 1:

                if row[1] == "":
                    row[1] = None

                    list_empty_accid.append(row)

            else:

                list_empty_accid.append(row)

            ####

####

####


#### Untouched Transactions table

cursor.execute('CREATE TABLE  IF NOT EXISTS orig_transactions AS SELECT * FROM transactions')

####

####

####


#### Map TransactionIds to AccountIds

cursor.execute('SELECT TransactionId,AccountId FROM transactions')

rows0 = cursor.fetchall()

map_ids = dict(rows0)

flipped_map_ids = {}

for key, value in map_ids.items():

    if value not in flipped_map_ids:

        flipped_map_ids[value] = [key]

    else:

        flipped_map_ids[value].append(key)

# print(flipped_map_ids)

####

####


#### Count number of transactions

cursor.execute('SELECT COUNT(TransactionId) from transactions')

num_transactions = cursor.fetchall()

num_transactions = list(itertools.chain(*num_transactions))[0]

####

####

####


#### More than one transaction for the same account on the same date

cursor.execute('''

               SELECT Date, AccountId, COUNT (*) as cnt

               FROM transactions

               GROUP BY Date, AccountId

               HAVING cnt > 1

               ''')

dup_dates = cursor.fetchall()

dup_dates_list = [row[0] for row in dup_dates]

####

####


#### Duplicated rows with the lowest id

cursor.execute('''

               SELECT t.*

               FROM transactions t

                        JOIN (SELECT Date, MIN (TransactionId) AS min_id

                              FROM transactions

                              GROUP BY Date

                              HAVING COUNT (*) > 1) sub
                             ON t.Date = sub.Date AND t.TransactionId = sub.min_id

               ORDER BY t.Date ASC

               ''')

# print(txns_dupdates_list)

####

####

####


#### Query to create table with duplicated transactions

cursor.execute('''

               SELECT t.*

               FROM transactions t

                        JOIN (SELECT Date, AccountId, MIN (TransactionId) AS min_id

                              FROM transactions

                              GROUP BY Date, AccountId

                              HAVING COUNT (*) > 1) sub
                             ON t.Date = sub.Date AND t.AccountId = sub.AccountId

               WHERE t.TransactionId != sub.min_id

               ORDER BY t.Date ASC

               ''')

txns_dupdates = cursor.fetchall()

txns_dupdates_list = [row[0:2] for row in txns_dupdates]

#### Table with duplicated transactions

cursor.execute('''CREATE TABLE IF NOT EXISTS DuplicateDates
(

    TransactionId
    INT
    PRIMARY
    KEY,

    AccountId
    INT,

    Date
    DATETIME,

    Amount
    INT,

    Currency
    INT,

    DebitCredit
    VARCHAR
                  (
    10
                  ),

    Status VARCHAR
                  (
                      255
                  ),

    Timezone VARCHAR
                  (
                      255
                  )

    )''')

####

####

####


#### Fill Table with duplicated transactions

cursor.execute('DELETE FROM DuplicateDates')

insert_query = '''

               INSERT INTO DuplicateDates

               (TransactionId, AccountId, Date, Amount, Currency, DebitCredit, Status, Timezone)

               VALUES (?, ?, ?, ?, ?, ?, ?, ?) \

               '''

cursor.executemany(insert_query, txns_dupdates)

####

####

####


#### Remove duplicated transactions from the table transactions

cursor.execute('''DELETE
                  FROM transactions

                  WHERE TransactionId IN (SELECT TransactionId
                                          FROM DuplicateDates)''')

####

####

####


#### Handle Null and Empty values

column_names_txn = [

    'TransactionId',

    'AccountId',

    'Date',

    'Amount',

    'Currency',

    'DebitCredit',

    'Status',

    'Timezone'

]

column_names_acc = [

    'AccountId',

    'Status',

    'Currency',

    'OpeningDate',

    'AccountTypeCode',

    'Timezone'

]

list_null_txn = []

for col in column_names_txn:
    query = f'SELECT COUNT(*) FROM transactions WHERE {col} IS NULL'

    cursor.execute(query)

    null_count = cursor.fetchone()[0]

    list_null_txn.append(null_count)

list_empty_txn = []

for col in column_names_txn:
    query0 = f'SELECT COUNT(*) AS CountEmpty FROM transactions WHERE {col} = ""'

    cursor.execute(query0)

    empty_count0 = cursor.fetchone()[0]

    list_empty_txn.append(empty_count0)

list_null_acc = []

for col in column_names_acc:
    query = f'SELECT COUNT(*) FROM accounts WHERE {col} IS NULL'

    cursor.execute(query)

    null_count = cursor.fetchone()[0]

    list_null_acc.append(null_count)

list_empty_acc = []

for col in column_names_acc:
    query = f'SELECT COUNT(*) FROM accounts WHERE {col} = ""'

    cursor.execute(query)

    empty_count1 = cursor.fetchone()[0]

    list_empty_acc.append(empty_count1)

# any empty string encountered is not a valid value, but rather a missing value

list_empty_null_acc = [x + y for x, y in zip(list_empty_acc, list_null_acc)]

list_empty_null_txn = [x + y for x, y in zip(list_empty_txn, list_null_txn)]

for col in column_names_txn:
    query = f'UPDATE transactions SET {col} = NULL WHERE {col} = ""'

    cursor.execute(query)

for col in column_names_acc:
    query = f'UPDATE accounts SET {col} = NULL WHERE {col} = ""'

    cursor.execute(query)

####

####

####


#### Query for mapping number of rows with x empy fields

query = '''SELECT (CASE WHEN AccountId IS NULL THEN 1 ELSE 0 END) + \
                  (CASE WHEN Status IS NULL THEN 1 ELSE 0 END) + \
                  (CASE WHEN Currency IS NULL THEN 1 ELSE 0 END) + \
                  (CASE WHEN OpeningDate IS NULL THEN 1 ELSE 0 END) + \
                  (CASE WHEN AccountTypeCode IS NULL THEN 1 ELSE 0 END) + \
                  (CASE WHEN Timezone IS NULL THEN 1 ELSE 0 END) AS num_nulls, \

                  COUNT(*)

           FROM accounts

           GROUP BY num_nulls

           ORDER BY num_nulls DESC '''

cursor.execute(query)

nulls_per_col_acc = cursor.fetchall()

nulls_per_col_acc = dict(nulls_per_col_acc)

for nulls in nulls_per_col_acc:
    nulls_per_col_acc[nulls] = f'{nulls_per_col_acc[nulls]} empty value(s)'

# print(nulls_per_col_acc)

####

####

####


#### If at least one row has more than one empty field

query = '''SELECT *

           FROM accounts

           WHERE ( \
                     (CASE WHEN AccountId IS NULL THEN 1 ELSE 0 END) + \
                     (CASE WHEN Status IS NULL THEN 1 ELSE 0 END) + \
                     (CASE WHEN Currency IS NULL THEN 1 ELSE 0 END) + \
                     (CASE WHEN OpeningDate IS NULL THEN 1 ELSE 0 END) + \
                     (CASE WHEN AccountTypeCode IS NULL THEN 1 ELSE 0 END) + \
                     (CASE WHEN Timezone IS NULL THEN 1 ELSE 0 END) \
                     ) > 1'''

cursor.execute(query)

more_one_null_acc = cursor.fetchall()

if more_one_null_acc:
    #### Create table with these rows

    cursor.execute('''

                   CREATE TABLE IF NOT EXISTS AccountsWithMoreThanOneNull
                   (

                       AccountId
                       INTEGER
                       PRIMARY
                       KEY,

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

    ####

    ####

    ####

    #### Fill table

    cursor.execute('DELETE FROM AccountsWithMoreThanOneNull')

    insert_query = '''

                   INSERT INTO AccountsWithMoreThanOneNull

                       (AccountID, Status, Currency, OpeningDate, AccountTypeCode, Timezone)

                   VALUES (?, ?, ?, ?, ?, ?) '''

    cursor.executemany(insert_query, more_one_null_acc)

    ####

    ####

    ####

    #### Remove those rows from accounts

    cursor.execute('DELETE FROM transactions WHERE AccountId IN (SELECT AccountId FROM AccountsWithMoreThanOneNull)')

    conn.commit()

    cursor.execute('''DELETE
                      FROM accounts

                      WHERE AccountId IN (SELECT AccountId
                                          FROM AccountsWithMoreThanOneNull)''')

####

####

####


conn.commit()

conn.close()