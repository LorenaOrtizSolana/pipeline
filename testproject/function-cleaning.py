import sqlite3
import difflib
from dateutil import parser
from datetime import timezone


def to_iso8601_preserve_tz(date_str):
    dt = parser.parse(date_str)
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.strftime('%Y-%m-%dT%H:%M:%S%z')[:-2] + ':' + dt.strftime('%z')[-2:]


def correct_date_column(conn, table, date_column, id_column):
    cursor = conn.cursor()
    cursor.execute(f'SELECT {id_column}, {date_column} FROM {table}')
    rows = cursor.fetchall()
    for row_id, date_str in rows:
        if date_str is not None:
            try:
                corrected_date = to_iso8601_preserve_tz(date_str)
                cursor.execute(
                    f'UPDATE {table} SET {date_column} = ? WHERE {id_column} = ?',
                    (corrected_date, row_id)
                )
            except Exception as e:
                cursor.execute(f'UPDATE transactions SET TransactionDate = NULL WHERE TransactionId = ?',
                               (transaction_id,))
    conn.commit()


def clean_and_flag_column(
        conn,
        table_name,
        column_name,
        correct_values,
        id_column='TransactionId'
):
    cursor = conn.cursor()

    # 1. Getting unique values
    cursor.execute(f'SELECT DISTINCT {column_name} FROM {table_name}')
    unique_values = [row[0] for row in cursor.fetchall() if row[0] is not None]

    # 2. Building mapping
    mapping = {}
    for val in unique_values:
        match = difflib.get_close_matches(val, correct_values, n=1, cutoff=0.6)
        if match:
            mapping[val] = match[0]
        else:
            mapping[val] = val

            # 3. Updating incorrect values
    for incorrect_value, correct_value in mapping.items():
        if incorrect_value != correct_value:
            query = f'UPDATE {table_name} SET {column_name} = ? WHERE {column_name} = ?'
            cursor.execute(query, (correct_value, incorrect_value))

            # 4. Finding incorrect IDs (for flagging)
    incorrect_values = [val for val in unique_values if val not in correct_values]
    if incorrect_values:
        placeholders = ','.join('?' for _ in incorrect_values)
        query = f'SELECT {id_column} FROM {table_name} WHERE {column_name} IN ({placeholders})'
        cursor.execute(query, incorrect_values)
        incorrect_ids = [row[0] for row in cursor.fetchall()]
    else:
        incorrect_ids = []

        # 5. Adding flag column if not exists
    flag_column = f'{column_name}Cleaned'
    try:
        cursor.execute(f'ALTER TABLE {table_name} ADD COLUMN {flag_column} INTEGER')
    except sqlite3.OperationalError:
        pass  # Column already exists

    # 6. Setting all to 0
    cursor.execute(f'UPDATE {table_name} SET {flag_column} = 0')

    # 7. Setting to 1 for incorrect IDs
    if incorrect_ids:
        placeholders = ','.join('?' for _ in incorrect_ids)
        query = f'UPDATE {table_name} SET {flag_column} = 1 WHERE {id_column} IN ({placeholders})'
        cursor.execute(query, incorrect_ids)

    conn.commit()
    # print(f"Cleaned column '{column_name}'. Mapping used: {mapping}")


conn = sqlite3.connect('test_db.db')

correct_date_column(
    conn,
    table='transactions',
    date_column='Date',
    id_column='TransactionId')

correct_date_column(
    conn,
    table='accounts',
    date_column='OpeningDate',
    id_column='AccountId')

clean_and_flag_column(
    conn,
    table_name='transactions',
    column_name='Status',
    correct_values=['BOOK', 'PENDING', 'REJECTED'],
    id_column='TransactionId'
)

clean_and_flag_column(
    conn,
    table_name='transactions',
    column_name='DebitCredit',
    correct_values=['DEBIT', 'CREDIT'],
    id_column='TransactionId'
)

clean_and_flag_column(
    conn,
    table_name='transactions',
    column_name='Timezone',
    correct_values=['Europe/Berlin', 'Europe/London', 'America/New_York'],
    id_column='TransactionId'
)

clean_and_flag_column(
    conn,
    table_name='accounts',
    column_name='Status',
    correct_values=['ACTIVE', 'CLOSED'],
    id_column='AccountId'
)

clean_and_flag_column(
    conn,
    table_name='accounts',
    column_name='Currency',
    correct_values=['EUR', 'USD', 'SEK'],
    id_column='AccountId'
)

clean_and_flag_column(
    conn,
    table_name='accounts',
    column_name='AccountTypeCode',
    correct_values=['CACC', 'LOAN', 'SAVG'],
    id_column='AccountId'
)