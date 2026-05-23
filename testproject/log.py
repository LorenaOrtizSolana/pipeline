import sqlite3
import csv
import itertools
import difflib
from dateutil import parser
from datetime import datetime, timezone
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import os


def log_change(conn, table_name, row_id, column_name, original_value, new_value, action, reason):
    try:
        cursor = conn.cursor()
        cursor.execute('''
                       CREATE TABLE IF NOT EXISTS cleaning_log
                       (
                           log_id
                           INTEGER
                           PRIMARY
                           KEY
                           AUTOINCREMENT,
                           table_name
                           TEXT,
                           row_id
                           TEXT,
                           column_name
                           TEXT,
                           original_value
                           TEXT,
                           new_value
                           TEXT,
                           action
                           TEXT,
                           reason
                           TEXT,
                           cleaned_at
                           TIMESTAMP
                           DEFAULT
                           CURRENT_TIMESTAMP
                       )
                       ''')
        cursor.execute('''
                       INSERT INTO cleaning_log
                       (table_name, row_id, column_name, original_value, new_value, action, reason)
                       VALUES (?, ?, ?, ?, ?, ?, ?)
                       ''', (table_name, str(row_id), column_name, str(original_value), str(new_value), action, reason))
        conn.commit()
    except Exception as e:
        pass


def invalid_transaction_dates(conn,
                              transactions_table='transactions',
                              accounts_table='accounts',
                              txn_id_col='TransactionId',
                              txn_acc_col='AccountId',
                              txn_date_col='Date',
                              acc_id_col='AccountID',
                              acc_open_col='OpeningDate'):
    cursor = conn.cursor()

    cursor.execute(f"PRAGMA table_info({transactions_table})")
    txn_columns = [row[1] for row in cursor.fetchall()]
    col_defs = ', '.join([f"{col} TEXT" for col in txn_columns])

    cursor.execute(f"""    
        SELECT t.*, a.{acc_open_col}  
        FROM {transactions_table} t    
        JOIN {accounts_table} a    
          ON t.{txn_acc_col} = a.{acc_id_col}    
        WHERE t.{txn_date_col} < a.{acc_open_col}    
    """)
    invalid_rows = cursor.fetchall()

    txn_id_idx = txn_columns.index(txn_id_col)
    for row in invalid_rows:
        log_change(
            conn=conn,
            table_name=transactions_table,
            row_id=row[txn_id_idx],
            column_name=txn_date_col,
            original_value=row[txn_columns.index(txn_date_col)],
            new_value='MOVED_TO_INVALID_TABLE',
            action='removed',
            reason=f'Transaction date before account opening date'
        )

    invalid_rows_trimmed = [row[:len(txn_columns)] for row in invalid_rows]

    new_table = f"{transactions_table}_invalid_date"
    cursor.execute(f"DROP TABLE IF EXISTS {new_table}")
    cursor.execute(f"CREATE TABLE {new_table} ({col_defs})")

    placeholders = ','.join(['?'] * len(txn_columns))
    cursor.executemany(
        f"INSERT INTO {new_table} VALUES ({placeholders})",
        invalid_rows_trimmed
    )

    invalid_ids = [row[txn_id_idx] for row in invalid_rows_trimmed]
    if invalid_ids:
        id_placeholders = ','.join(['?'] * len(invalid_ids))
        cursor.execute(
            f"DELETE FROM {transactions_table} WHERE {txn_id_col} IN ({id_placeholders})",
            invalid_ids
        )

    conn.commit()


def move_and_remove_future_dates(conn, table, date_column, id_column='rowid'):
    cursor = conn.cursor()

    cursor.execute(f"PRAGMA table_info({table})")
    columns = [row[1] for row in cursor.fetchall()]
    col_defs = ', '.join([f"{col} TEXT" for col in columns])

    now = datetime.now().isoformat()

    cursor.execute(
        f"SELECT * FROM {table} WHERE {date_column} > ?",
        (now,)
    )
    future_rows = cursor.fetchall()

    id_idx = columns.index(id_column)
    date_idx = columns.index(date_column)
    for row in future_rows:
        log_change(
            conn=conn,
            table_name=table,
            row_id=row[id_idx],
            column_name=date_column,
            original_value=row[date_idx],
            new_value='MOVED_TO_FUTURE_TABLE',
            action='removed',
            reason=f'Date is in the future (>{now})'
        )

    new_table = f"{table}_future_{date_column}"
    cursor.execute(f"DROP TABLE IF EXISTS {new_table}")
    cursor.execute(f"CREATE TABLE {new_table} ({col_defs})")

    placeholders = ','.join(['?'] * len(columns))
    cursor.executemany(
        f"INSERT INTO {new_table} VALUES ({placeholders})",
        future_rows
    )

    future_ids = [row[id_idx] for row in future_rows]
    if future_ids:
        id_placeholders = ','.join(['?'] * len(future_ids))
        cursor.execute(
            f"DELETE FROM {table} WHERE {id_column} IN ({id_placeholders})",
            future_ids
        )

    conn.commit()


def clean_nonnumeric_rows(conn, table, column, id_column='rowid'):
    cursor = conn.cursor()

    cursor.execute(f"PRAGMA table_info({table})")
    col_info = {row[1]: row[2].upper() for row in cursor.fetchall()}
    col_type = col_info.get(column)
    if col_type in ('INTEGER', 'REAL'):
        return

    cursor.execute(f"""  
        SELECT * FROM {table}  
        WHERE typeof({column}) NOT IN ('integer', 'real')  
    """)
    nonnumeric_rows = cursor.fetchall()
    if not nonnumeric_rows:
        print(f"No non-numeric values found in column '{column}'.")
        return

    cursor.execute(f"PRAGMA table_info({table})")
    columns = [row[1] for row in cursor.fetchall()]
    col_defs = ', '.join([f"{col} TEXT" for col in columns])

    id_idx = columns.index(id_column)
    col_idx = columns.index(column)
    for row in nonnumeric_rows:
        log_change(
            conn=conn,
            table_name=table,
            row_id=row[id_idx],
            column_name=column,
            original_value=row[col_idx],
            new_value='MOVED_TO_NONNUMERIC_TABLE',
            action='removed',
            reason=f'Value is not numeric (type: {type(row[col_idx]).__name__})'
        )

    new_table = f"{table}_nonnumeric_{column}"
    cursor.execute(f"DROP TABLE IF EXISTS {new_table}")
    cursor.execute(f"CREATE TABLE {new_table} ({col_defs})")

    placeholders = ','.join(['?'] * len(columns))
    cursor.executemany(
        f"INSERT INTO {new_table} VALUES ({placeholders})",
        nonnumeric_rows
    )

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
            original = date_str
            try:
                corrected_date = to_iso8601_preserve_tz(date_str)
                if str(original) != str(corrected_date):
                    log_change(
                        conn=conn,
                        table_name=table,
                        row_id=row_id,
                        column_name=date_column,
                        original_value=original,
                        new_value=corrected_date,
                        action='corrected',
                        reason='Date format converted to ISO8601 with timezone'
                    )
                cursor.execute(
                    f'UPDATE {table} SET {date_column} = ? WHERE {id_column} = ?',
                    (corrected_date, row_id)
                )
            except Exception as e:
                log_change(
                    conn=conn,
                    table_name=table,
                    row_id=row_id,
                    column_name=date_column,
                    original_value=original,
                    new_value='NULL',
                    action='set_null',
                    reason=f'Could not parse date: {str(e)}'
                )
                cursor.execute(f'UPDATE {table} SET {date_column} = NULL WHERE {id_column} = ?', (row_id,))
    conn.commit()


def clean_and_flag_column(
        conn,
        table_name,
        column_name,
        correct_values,
        id_column='TransactionId'
):
    cursor = conn.cursor()

    cursor.execute(f'SELECT DISTINCT {column_name} FROM {table_name}')
    unique_values = [row[0] for row in cursor.fetchall() if row[0] is not None]

    mapping = {}
    for val in unique_values:
        match = difflib.get_close_matches(val, correct_values, n=1, cutoff=0.6)
        if match:
            mapping[val] = match[0]
        else:
            mapping[val] = val

    affected_rows_info = []
    for incorrect_value, correct_value in mapping.items():
        if incorrect_value != correct_value:
            cursor.execute(f'SELECT {id_column} FROM {table_name} WHERE {column_name} = ?', (incorrect_value,))
            rows = cursor.fetchall()
            for row in rows:
                affected_rows_info.append({
                    'row_id': row[0],
                    'original': incorrect_value,
                    'new': correct_value
                })

    for incorrect_value, correct_value in mapping.items():
        if incorrect_value != correct_value:
            query = f'UPDATE {table_name} SET {column_name} = ? WHERE {column_name} = ?'
            cursor.execute(query, (correct_value, incorrect_value))

    for info in affected_rows_info:
        log_change(
            conn=conn,
            table_name=table_name,
            row_id=info['row_id'],
            column_name=column_name,
            original_value=info['original'],
            new_value=info['new'],
            action='corrected',
            reason=f'Value mapped from "{info["original"]}" to closest valid: {correct_values}'
        )

    incorrect_values = [val for val in unique_values if val not in correct_values]
    if incorrect_values:
        placeholders = ','.join('?' for _ in incorrect_values)
        query = f'SELECT {id_column} FROM {table_name} WHERE {column_name} IN ({placeholders})'
        cursor.execute(query, incorrect_values)
        incorrect_ids = [row[0] for row in cursor.fetchall()]
    else:
        incorrect_ids = []

    flag_column = f'{column_name}Cleaned'
    try:
        cursor.execute(f'ALTER TABLE {table_name} ADD COLUMN {flag_column} INTEGER')
    except sqlite3.OperationalError:
        pass

    cursor.execute(f'UPDATE {table_name} SET {flag_column} = 0')

    if incorrect_ids:
        placeholders = ','.join('?' for _ in incorrect_ids)
        query = f'UPDATE {table_name} SET {flag_column} = 1 WHERE {id_column} IN ({placeholders})'
        cursor.execute(query, incorrect_ids)

    conn.commit()


def create_log_table(conn):
    cursor = conn.cursor()
    cursor.execute('''
                   CREATE TABLE IF NOT EXISTS cleaning_log
                   (
                       log_id
                       INTEGER
                       PRIMARY
                       KEY
                       AUTOINCREMENT,
                       table_name
                       TEXT
                       NOT
                       NULL,
                       row_id
                       TEXT
                       NOT
                       NULL,
                       column_name
                       TEXT
                       NOT
                       NULL,
                       original_value
                       TEXT,
                       new_value
                       TEXT,
                       action
                       TEXT,
                       reason
                       TEXT,
                       cleaned_at
                       TIMESTAMP
                       DEFAULT
                       CURRENT_TIMESTAMP
                   )
                   ''')
    conn.commit()
    print("✓ cleaning_log table ready")


def generate_summary_report(conn, output_dir="cleaning_reports"):
    os.makedirs(output_dir, exist_ok=True)

    df = pd.read_sql_query("SELECT * FROM cleaning_log", conn)

    if df.empty:
        print("No cleaning actions logged yet.")
        return None

    summary = {
        "Total changes": len(df),
        "Tables affected": df['table_name'].nunique(),
        "Columns affected": df['column_name'].nunique(),
        "Most cleaned table": df['table_name'].mode()[0] if not df.empty else "N/A",
        "Most cleaned column": df['column_name'].mode()[0] if not df.empty else "N/A",
        "Most common action": df['action'].mode()[0] if not df.empty else "N/A",
        "Date range": f"{df['cleaned_at'].min()} to {df['cleaned_at'].max()}"
    }

    with open(f"{output_dir}/summary_report.txt", "w", encoding="utf-8") as f:
        f.write("CLEANING LOG SUMMARY REPORT\n")
        f.write("=" * 40 + "\n")
        f.write(f"Generated: {datetime.now()}\n\n")
        for key, value in summary.items():
            f.write(f"{key}: {value}\n")

    print(f"✓ Summary report saved to {output_dir}/summary_report.txt")
    return df


def generate_visualizations(df, output_dir="cleaning_reports"):
    os.makedirs(output_dir, exist_ok=True)

    if df.empty:
        print("No data to visualize.")
        return

    sns.set_style("whitegrid")

    plt.figure(figsize=(10, 6))
    table_counts = df['table_name'].value_counts()
    sns.barplot(x=table_counts.values, y=table_counts.index, hue=table_counts.index, palette="Blues_d", legend=False)
    plt.title('Number of Cleaning Changes by Table', fontsize=14)
    plt.xlabel('Number of changes')
    plt.tight_layout()
    plt.savefig(f"{output_dir}/1_changes_by_table.png", dpi=150)
    plt.close()
    print(f"✓ Saved: {output_dir}/1_changes_by_table.png")

    plt.figure(figsize=(12, 6))
    col_counts = df['column_name'].value_counts().head(10)
    sns.barplot(x=col_counts.values, y=col_counts.index, hue=col_counts.index, palette="Greens_d", legend=False)
    plt.title('Top 10 Columns with Most Changes', fontsize=14)
    plt.xlabel('Number of changes')
    plt.tight_layout()
    plt.savefig(f"{output_dir}/2_changes_by_column.png", dpi=150)
    plt.close()
    print(f"✓ Saved: {output_dir}/2_changes_by_column.png")

    plt.figure(figsize=(8, 8))
    action_counts = df['action'].value_counts()
    plt.pie(action_counts.values, labels=action_counts.index, autopct='%1.1f%%', startangle=90)
    plt.title('Types of Cleaning Actions', fontsize=14)
    plt.tight_layout()
    plt.savefig(f"{output_dir}/3_actions_pie.png", dpi=150)
    plt.close()
    print(f"✓ Saved: {output_dir}/3_actions_pie.png")

    if 'cleaned_at' in df.columns:
        plt.figure(figsize=(10, 5))
        df['date_only'] = pd.to_datetime(df['cleaned_at']).dt.date
        time_counts = df['date_only'].value_counts().sort_index()
        plt.plot(time_counts.index, time_counts.values, marker='o', linestyle='-', color='purple')
        plt.title('Cleaning Activity Over Time', fontsize=14)
        plt.xlabel('Date')
        plt.ylabel('Number of changes')
        plt.xticks(rotation=45)
        plt.tight_layout()
        plt.savefig(f"{output_dir}/4_changes_over_time.png", dpi=150)
        plt.close()
        print(f"✓ Saved: {output_dir}/4_changes_over_time.png")

    plt.figure(figsize=(10, 6))
    cross_tab = pd.crosstab(df['table_name'], df['action'])
    sns.heatmap(cross_tab, annot=True, fmt='d', cmap='YlOrRd')
    plt.title('Cleaning Actions by Table', fontsize=14)
    plt.tight_layout()
    plt.savefig(f"{output_dir}/5_heatmap_table_action.png", dpi=150)
    plt.close()
    print(f"✓ Saved: {output_dir}/5_heatmap_table_action.png")


def generate_exception_report(conn, output_dir="cleaning_reports"):
    df = pd.read_sql_query("SELECT * FROM cleaning_log", conn)

    if df.empty:
        print("No cleaning actions to report.")
        return

    os.makedirs(output_dir, exist_ok=True)

    with open(f"{output_dir}/exception_report.txt", "w", encoding="utf-8") as f:
        f.write("EXCEPTION REPORT - DATA CLEANING PIPELINE\n")
        f.write("=" * 50 + "\n")
        f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")

        f.write("RESUMEN EJECUTIVO\n")
        f.write("-" * 20 + "\n")
        f.write(f"Total de cambios realizados: {len(df)}\n")
        f.write(f"Tablas afectadas: {df['table_name'].unique().tolist()}\n")
        f.write(f"Columnas afectadas: {df['column_name'].unique().tolist()}\n\n")

        f.write("DETALLE POR TIPO DE ERROR\n")
        f.write("-" * 25 + "\n")

        for reason, group in df.groupby('reason'):
            f.write(f"\n[{reason}]\n")
            f.write(f"  Cantidad: {len(group)}\n")
            f.write(f"  Ejemplo: {group.iloc[0]['table_name']}.{group.iloc[0]['column_name']} ")
            f.write(f"('{group.iloc[0]['original_value']}' → '{group.iloc[0]['new_value']}')\n")

        f.write("\n" + "=" * 50 + "\n")
        f.write("FIN DEL REPORTE\n")

    print(f"✓ Exception report saved to {output_dir}/exception_report.txt")


def export_log_to_csv(conn, output_dir="cleaning_reports"):
    df = pd.read_sql_query("SELECT * FROM cleaning_log", conn)

    if df.empty:
        print("No log entries to export.")
        return

    csv_path = f"{output_dir}/cleaning_log_export.csv"
    df.to_csv(csv_path, index=False)
    print(f"✓ Full cleaning log exported to {csv_path}")


def run_cleaning_log():
    print("\n" + "=" * 50)
    print("CLEANING LOG GENERATOR")
    print("=" * 50 + "\n")

    conn = sqlite3.connect('test_db.db')

    create_log_table(conn)

    print("\nGenerating reports...\n")
    df = generate_summary_report(conn)

    if df is not None and not df.empty:
        generate_visualizations(df)
        generate_exception_report(conn)
        export_log_to_csv(conn)
    else:
        print("\n⚠️  No cleaning log entries found.")
        print("   Make sure your cleaning functions call log_change()")

    conn.close()

    print("\n" + "=" * 50)
    print("CLEANING LOG COMPLETE")
    print(f"Check the 'cleaning_reports' folder for outputs")
    print("=" * 50)


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

move_and_remove_future_dates(conn, 'transactions', 'Date', id_column='TransactionId')
move_and_remove_future_dates(conn, 'accounts', 'OpeningDate', id_column='AccountId')

invalid_transaction_dates(conn)

conn.close()

run_cleaning_log()