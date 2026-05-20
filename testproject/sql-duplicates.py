import sqlite3
import csv
import itertools

conn = sqlite3.connect('test_db.db')
conn.execute("PRAGMA foreign_keys = ON")
cursor = conn.cursor()

# Count number of transactions
cursor.execute('SELECT COUNT(TransactionId) from transactions')
num_transactions = cursor.fetchall()
num_transactions = list(itertools.chain(*num_transactions))[0]

# More than one transaction for the same account on the same date
cursor.execute(''' 
    SELECT Date, AccountId, COUNT(*) as cnt   
    FROM transactions   
    GROUP BY Date, AccountId   
    HAVING cnt > 1 
''')
dup_dates = cursor.fetchall()
dup_dates_list = [row[0] for row in dup_dates]

# Duplicated rows with the lowest id
cursor.execute(''' 
    SELECT t.* 
    FROM transactions t 
    JOIN ( 
        SELECT Date, MIN(TransactionId) AS min_id 
        FROM transactions 
        GROUP BY Date 
        HAVING COUNT(*) > 1 
    ) sub 
    ON t.Date = sub.Date AND t.TransactionId = sub.min_id 
    ORDER BY t.Date ASC 
''')

# Query to create table with duplicated transactions
cursor.execute('''
    SELECT t.* 
    FROM transactions t 
    JOIN ( 
        SELECT Date, AccountId, MIN(TransactionId) AS min_id 
        FROM transactions 
        GROUP BY Date, AccountId 
        HAVING COUNT(*) > 1 
    ) sub 
    ON t.Date = sub.Date AND t.AccountId = sub.AccountId 
    WHERE t.TransactionId != sub.min_id 
    ORDER BY t.Date ASC
''')
txns_dupdates = cursor.fetchall()
txns_dupdates_list = [row[0:2] for row in txns_dupdates]

# Table with duplicated transactions
cursor.execute('''CREATE TABLE IF NOT EXISTS DuplicateDates ( 
    TransactionId INT PRIMARY KEY, 
    AccountId INT, 
    Date DATETIME, 
    Amount INT, 
    Currency INT, 
    DebitCredit VARCHAR(10), 
    Status VARCHAR(255), 
    Timezone VARCHAR(255) 
)''')

# Fill Table with duplicated transactions
cursor.execute('DELETE FROM DuplicateDates')
insert_query = ''' 
    INSERT INTO DuplicateDates 
    (TransactionId, AccountId, Date, Amount, Currency, DebitCredit, Status, Timezone) 
    VALUES (?, ?, ?, ?, ?, ?, ?, ?) 
'''
cursor.executemany(insert_query, txns_dupdates)

# Remove duplicated transactions from the table transactions
cursor.execute('''DELETE FROM transactions 
WHERE TransactionId IN ( 
    SELECT TransactionId FROM DuplicateDates 
)''')

conn.commit()
conn.close()