import sqlite3
import csv
import itertools
import difflib

#import rapidfuzz
#from rapidfuzz import process

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
    distinct_dict[col] =  list_dist_per_col
#print(distinct_dict)
####

####Set of unique values, transactions
distinct_dict1 = {}
for col in column_names_txn:
    query = f'''SELECT DISTINCT {col}
FROM transactions'''
    cursor.execute(query)
    dist_per_col1 = cursor.fetchall()
    list_dist_per_col1 = [tup[0] for tup in dist_per_col1]
    distinct_dict1[col] =  list_dist_per_col1
#print(distinct_dict1)
####
####
####

conn.commit()
conn.close()