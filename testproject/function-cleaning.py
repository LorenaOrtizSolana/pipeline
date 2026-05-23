import sqlite3
import difflib
from dateutil import parser
from datetime import timezone
import sqlite3


def clean_nonnumeric_rows(conn, table, column, id_column='rowid'):
    cursor = conn.cursor()

    # check column type
    cursor.execute(f"PRAGMA table_info({table})")
    col_info = {row[1]: row[2].upper() for row in cursor.fetchall()}
    col_type = col_info.get(column)
    if col_type in ('INTEGER', 'REAL'):
        return
        ####

    # neither 'integer' nor 'real' rows
    cursor.execute(f"""  
        SELECT * FROM {table}  
        WHERE typeof({column}) NOT IN ('integer', 'real')  
    """)
    nonnumeric_rows = cursor.fetchall()
    if not nonnumeric_rows:
        print(f"No non-numeric values found in column '{column}'.")
        return

        # column names for table creation
    cursor.execute(f"PRAGMA table_info({table})")
    columns = [row[1] for row in cursor.fetchall()]
    col_defs = ', '.join([f"{col} TEXT" for col in columns])  # Use TEXT for all for simplicity
    ####

    ####
    new_table = f"{table}_nonnumeric_{column}"
    cursor.execute(f"DROP TABLE IF EXISTS {new_table}")
    cursor.execute(f"CREATE TABLE {new_table} ({col_defs})")
    ####

    ####
    placeholders = ','.join(['?'] * len(columns))
    cursor.executemany(
        f"INSERT INTO {new_table} VALUES ({placeholders})",
        nonnumeric_rows
    )
    ####

    # remove non-numeric rows from original table
    id_idx = columns.index(id_column)
    nonnumeric_ids = [row[id_idx] for row in nonnumeric_rows]
    if nonnumeric_ids:
        id_placeholders = ','.join(['?'] * len(nonnumeric_ids))
        cursor.execute(
            f"DELETE FROM {table} WHERE {id_column} IN ({id_placeholders})",
            nonnumeric_ids
        )

    conn.commit()


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

clean_nonnumeric_rows(conn, 'transactions', 'Amount', id_column='TransactionId')

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

conn.close()
