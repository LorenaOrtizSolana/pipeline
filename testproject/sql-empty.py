import sqlite3
import csv
import itertools
from datetime import datetime
from dateutil import parser


conn = sqlite3.connect('test_db.db')
conn.execute("PRAGMA foreign_keys = ON")
cursor = conn.cursor()

#### Handle Null and Empty values

column_names_txn = [
    'TransactionId',
    'AccountId',
    'Date',
    'Amount',
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

#### Query for mapping number of rows with x empty fields, accounts

query = '''SELECT  
    (CASE WHEN AccountId IS NULL THEN 1 ELSE 0 END) + 
    (CASE WHEN Status IS NULL THEN 1 ELSE 0 END) + 
    (CASE WHEN Currency IS NULL THEN 1 ELSE 0 END) + 
    (CASE WHEN OpeningDate IS NULL THEN 1 ELSE 0 END) + 
    (CASE WHEN AccountTypeCode IS NULL THEN 1 ELSE 0 END) + 
    (CASE WHEN Timezone IS NULL THEN 1 ELSE 0 END) AS num_nulls, 
    COUNT(*)  
FROM accounts 
GROUP BY num_nulls
ORDER BY num_nulls DESC
'''
cursor.execute(query)
nulls_per_col_acc = cursor.fetchall()
nulls_per_col_acc = dict(nulls_per_col_acc)
for nulls in nulls_per_col_acc:
    nulls_per_col_acc[nulls] = f'{nulls_per_col_acc[nulls]} empty value(s)'

####
####
####

#### Query for mapping number of rows with x empty fields, transactions

query = '''SELECT  
    (CASE WHEN TransactionId IS NULL THEN 1 ELSE 0 END) + 
    (CASE WHEN AccountId IS NULL THEN 1 ELSE 0 END) + 
    (CASE WHEN Date IS NULL THEN 1 ELSE 0 END) + 
    (CASE WHEN Amount IS NULL THEN 1 ELSE 0 END) + 
    (CASE WHEN DebitCredit IS NULL THEN 1 ELSE 0 END) + 
    (CASE WHEN Status IS NULL THEN 1 ELSE 0 END) +
    (CASE WHEN Timezone IS NULL THEN 1 ELSE 0 END) AS num_nulls, 
    COUNT(*)  
FROM transactions
GROUP BY num_nulls
ORDER BY num_nulls DESC
'''
cursor.execute(query)
nulls_per_col_txn = cursor.fetchall()
nulls_per_col_txn = dict(nulls_per_col_txn)
for nulls in nulls_per_col_txn:
    nulls_per_col_txn[nulls] = f'{nulls_per_col_txn[nulls]} empty value(s)'

####
####
####

###### Imputation: accounts

#### Impute empty Status field
#### If Status in accounts is empty check if last transaction happened within a certain period
#### and update it

query = '''UPDATE accounts 
SET Status = 'OPEN' 
WHERE Status IS NULL 
AND EXISTS ( 
    SELECT 1 
    FROM transactions t 
    WHERE t.AccountId = accounts.AccountId 
    AND t.Date >= DATE('now', '-90 days') 
) 
'''
cursor.execute(query)

####

#### Impute Timezone

query = '''SELECT AccountId, OpeningDate
    FROM accounts
    WHERE Timezone IS NULL
'''
cursor.execute(query)
empty_tzn = cursor.fetchall()
empty_tzn = dict(empty_tzn)  # could overwrite same accountid

tzn_dict = {}
for key, value in empty_tzn.items():
    if value is not None:
        value = parser.parse(value)
    try:
        tzn_dict[key] = value.tzname() if value.tzinfo else 'UTC'
    except Exception as e:
        tzn_dict[key] = None

for key, value in tzn_dict.items():
    if value:
        query = '''UPDATE accounts SET Timezone = ? WHERE AccountId = ?'''
        cursor.execute(query, (value, key))

####

###### Imputation: transactions

#### Fix and impute value of Debit/Credit

query = '''UPDATE transactions
    SET DebitCredit = CASE
        WHEN Amount < 0 THEN 'DEBIT'
        WHEN Amount > 0 THEN 'CREDIT'
        ELSE NULL
    END
'''
cursor.execute(query)

query = '''UPDATE transactions
    SET Amount = ABS(Amount)
'''
cursor.execute(query)

####

#### Impute Timezone

query = '''SELECT TransactionId, Date
    FROM transactions
    WHERE Timezone IS NULL
'''
cursor.execute(query)
empty_tzn1 = cursor.fetchall()
empty_tzn1 = dict(empty_tzn1)  # could overwrite same transactionid

tzn_dict1 = {}
for key, value in empty_tzn1.items():
    if value is not None:
        value = parser.parse(value)
    try:
        tzn_dict1[key] = value.tzname() if value.tzinfo else 'UTC'
    except Exception as e:
        tzn_dict1[key] = None

for key, value in tzn_dict1.items():
    if value:
        query = '''UPDATE transactions SET Timezone = ? WHERE TransactionId = ?'''
        cursor.execute(query, (value, key))

####
####
####

###### Remove rows with more than one NULL field from accounts

query = '''SELECT AccountId, Status, Currency, OpeningDate, AccountTypeCode, Timezone  
FROM accounts  
WHERE   
    ( 
        (CASE WHEN AccountId IS NULL THEN 1 ELSE 0 END) +   
        (CASE WHEN Status IS NULL THEN 1 ELSE 0 END) +   
        (CASE WHEN Currency IS NULL THEN 1 ELSE 0 END) +   
        (CASE WHEN OpeningDate IS NULL THEN 1 ELSE 0 END) +   
        (CASE WHEN AccountTypeCode IS NULL THEN 1 ELSE 0 END) +   
        (CASE WHEN Timezone IS NULL THEN 1 ELSE 0 END)   
    ) > 1'''
cursor.execute(query)
more_one_null_acc = cursor.fetchall()

if more_one_null_acc:
    # Create table with these rows
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS AccountsWithMoreThanOneNull (   
            AccountId INTEGER PRIMARY KEY,   
            Status VARCHAR(255),   
            Currency VARCHAR(3),   
            OpeningDate DATETIME,   
            AccountTypeCode CHAR(10),   
            Timezone VARCHAR(255)   
        )   
    ''')

    # Fill table
    cursor.execute('DELETE FROM AccountsWithMoreThanOneNull')
    insert_query = ''' 
        INSERT INTO AccountsWithMoreThanOneNull 
        (AccountID, Status, Currency, OpeningDate, AccountTypeCode, Timezone) 
        VALUES (?, ?, ?, ?, ?, ?)
    '''
    cursor.executemany(insert_query, more_one_null_acc)

    # Remove those rows from accounts
    cursor.execute('DELETE FROM transactions WHERE AccountId IN (SELECT AccountId FROM AccountsWithMoreThanOneNull)')
    conn.commit()

    cursor.execute('''DELETE FROM accounts 
    WHERE AccountId IN ( 
        SELECT AccountId FROM AccountsWithMoreThanOneNull 
    )''')

####
####
####

conn.commit()
conn.close()
