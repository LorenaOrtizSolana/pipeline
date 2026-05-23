# Banking Data Pipeline - Data Cleaning and Audit Log

**Author:** Lorena Ortiz Solana
**Role:** Data Science / Analytics Candidate (Bachelor Level)
**Focus:** Fintech / Banking - Data Quality, SQL, Python, Auditability

## Project Overview

This project simulates an end-to-end data pipeline for banking transactions. It is designed to demonstrate skills that are directly relevant for banks and fintechs:

- Generating realistic transaction data with intentional errors
- Loading data into a normalized SQLite database with foreign keys
- Cleaning the data step by step (duplicates, nulls, future dates, typos)
- Recording every change in a cleaning log for full auditability
- Creating visual reports that prove data quality improved

The pipeline is reproducible (fixed random seed), idempotent, and includes an exception report for manual review.

## Pipeline Structure

| Script | Purpose |
|--------|---------|
| `create-csv.py` | Simulates 150 accounts and transactions with realistic errors (nulls, duplicates, wrong formats, future dates). Uses seed(42). |
| `sql-filltables.py` | Creates SQLite tables (accounts, transactions) with foreign keys and inserts the CSV data. Saves original copies as orig_accounts and orig_transactions. |
| `sql-duplicates.py` | Detects and moves duplicate transactions (same account and same date) to a separate table. |
| `sql-empty.py` | Handles NULL and empty strings. Imputes missing timezones based on dates. Removes rows with too many missing fields. |
| `function_cleaning.py` | Core cleaning logic: fixes date formats, corrects categorical values with fuzzy matching, moves future and invalid dates to error tables, and logs every change to cleaning_log. |
| `balance.py` | Maintains account balances via SQL triggers on insert, update, and delete of transactions. |
| `cleaning_log.py` | Reads the cleaning_log table, generates summary statistics, exception report, and 5 data quality visualizations. |

## What the Cleaning Log Captures

For each change, the log records:

- Table and row ID
- Column name
- Original value to new value
- Action (corrected, removed, set_null)
- Reason (e.g., "Value not in allowed list")
- Timestamp

This is auditor-ready.

## Outputs (saved in cleaning_reports folder)

| File | Description |
|------|-------------|
| `summary_report.txt` | Text summary of total changes, most cleaned table and column, etc. |
| `exception_report.txt` | Human-readable report (English and Spanish) grouped by error type. |
| `cleaning_log_export.csv` | Full log as CSV. |
| `1_changes_by_table.png` | Bar chart of changes per table. |
| `2_changes_by_column.png` | Bar chart of changes per column (top 10). |
| `3_actions_pie.png` | Pie chart of action types (corrected vs removed). |
| `4_changes_over_time.png` | Cleaning activity over time (if multiple runs). |
| `5_heatmap_table_action.png` | Heatmap showing which tables required which actions. |

## How to Run the Pipeline

### 1. Requirements

```bash
pip install pandas matplotlib seaborn python-dateutil pytz
