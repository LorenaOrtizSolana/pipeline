import sqlite3
import csv
import itertools
import difflib

# import rapidfuzz
# from rapidfuzz import process

conn = sqlite3.connect('test_db.db')
conn.execute("PRAGMA foreign_keys = ON")
cursor = conn.cursor()

column_names_txn = [
    'DebitCredit',
    'Status',
    'Timezone'
]

column_names_acc = [
    'Status',
    'Currency',
    'AccountTypeCode',
    'Timezone'
]

#### Set of unique values, accounts
distinct_dict = {}
for col in column_names_acc:
    query = f'''SELECT DISTINCT {col} 
FROM accounts'''
    cursor.execute(query)
    dist_per_col = cursor.fetchall()
    list_dist_per_col = [tup[0] for tup in dist_per_col]
    distinct_dict[col] = list_dist_per_col
# print(distinct_dict)
####

####Set of unique values, transactions
distinct_dict1 = {}
for col in column_names_txn:
    query = f'''SELECT DISTINCT {col}
FROM transactions'''
    cursor.execute(query)
    dist_per_col1 = cursor.fetchall()
    list_dist_per_col1 = [tup[0] for tup in dist_per_col1]
    distinct_dict1[col] = list_dist_per_col1
# print(distinct_dict1)
####
####
####

##### Transactions
#### Fix Status values from transactions
correct_status_values = ['BOOK', 'PENDING', 'REJECTED']
unique_status_values = distinct_dict1['Status']
incorrect_status_values = [item for item in unique_status_values if item not in correct_status_values]
values_not_none = [item for item in unique_status_values if item is not None]
####

####
mapping = {}
for val in values_not_none:
    match = difflib.get_close_matches(val, correct_status_values, n=1, cutoff=0.6)
    if match:
        mapping[val] = match[0]
    # print(mapping)

inv_mapping = {}
for val in correct_status_values:
    temp_list = [k for k, v in mapping.items() if v == val]
    inv_mapping[val] = temp_list
# print(inv_mapping)
####

####
placeholders = ','.join('?' for _ in incorrect_status_values)
query = f'''SELECT TransactionId FROM transactions WHERE Status IN ({placeholders})'''
cursor.execute(query, incorrect_status_values)
incorrect_ids = cursor.fetchall()
incorrect_ids = [tup[0] for tup in incorrect_ids]
####

####
for incorrect_value, correct_value in mapping.items():
    if incorrect_value != correct_value:
        query = '''UPDATE transactions \
                   SET Status = ? \
                   WHERE Status = ?'''
        cursor.execute(query, (correct_value, incorrect_value))
####

####
try:
    cursor.execute('ALTER TABLE transactions ADD COLUMN StatusCleaned INTEGER')
except sqlite3.OperationalError:
    pass

cursor.execute('UPDATE transactions SET StatusCleaned = 0')
if incorrect_ids:
    placeholders = ','.join('?' for _ in incorrect_ids)
    query = f'UPDATE transactions SET StatusCleaned = 1 WHERE TransactionId IN ({placeholders})'
    cursor.execute(query, incorrect_ids)
####
####

#### Fix DebitCredit values
####
####

conn.commit()
conn.close()