import sqlite3
import csv
import itertools

conn = sqlite3.connect('test_db.db')
conn.execute("PRAGMA foreign_keys = ON")
cursor = conn.cursor()

# Handle Null and Empty values
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

# Query for mapping number of rows with x empty fields
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
ORDER BY num_nulls DESC '''
cursor.execute(query)
nulls_per_col_acc = cursor.fetchall()
nulls_per_col_acc = dict(nulls_per_col_acc)
for nulls in nulls_per_col_acc:
    nulls_per_col_acc[nulls] = f'{nulls_per_col_acc[nulls]} empty value(s)'

# If at least one row has more than one empty field
query = '''SELECT *   
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
            Currency INTEGER,   
            OpeningDate DATETIME,   
            AccountTypeCode CHAR(10),   
            Timezone VARCHAR(255)   
        )   
    ''')

    # Fill table
    cursor.execute('DELETE FROM AccountsWithMoreThanOneNull')
    insert_query = ''' 
        INSERT INTO AccountsWithMoreThanOneNull 
        (AccountID,Status,Currency,OpeningDate,AccountTypeCode,Timezone) 
        VALUES (?, ?, ?, ?, ?, ?) '''
    cursor.executemany(insert_query, more_one_null_acc)

    # Remove those rows from accounts
    cursor.execute('DELETE FROM transactions WHERE AccountId IN (SELECT AccountId FROM AccountsWithMoreThanOneNull)')
    conn.commit()

    cursor.execute('''DELETE FROM accounts 
    WHERE AccountId IN ( 
        SELECT AccountId FROM AccountsWithMoreThanOneNull 
    )''')

conn.commit()
conn.close()