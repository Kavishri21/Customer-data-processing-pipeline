"""
Data Profiling Module for Customer Data Processing & Analytics Pipeline

Examines raw datasets (customers.csv and transactions.json) before cleaning.
Identifies data quality issues such as nulls, duplicates, bad formats, and orphaned keys.
Generates profiling summary and CSV reports.
"""

import os
import re
import json
import warnings
import pandas as pd

warnings.filterwarnings('ignore', category=UserWarning)


def is_valid_email(email):
    """Simple regex to check basic email validity."""
    if not isinstance(email, str) or not email.strip():
        return False
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(pattern, email.strip()))


def profile_raw_data(customers_path="data/raw/customers.csv",
                     transactions_path="data/raw/transactions.json",
                     output_dir="reports"):
    """Profiles raw datasets and writes reports."""
    os.makedirs(output_dir, exist_ok=True)
    report_lines = []
    report_lines.append("=" * 60)
    report_lines.append("DATA PROFILING REPORT")
    report_lines.append("=" * 60)

    # 1. Profile Customers
    if not os.path.exists(customers_path):
        raise FileNotFoundError(f"Customer raw file not found at {customers_path}")
    
    df_cust = pd.read_csv(customers_path)
    report_lines.append("\n--- RAW CUSTOMERS DATASET ---")
    report_lines.append(f"Row count    : {len(df_cust)}")
    report_lines.append(f"Column count : {len(df_cust.columns)}")
    report_lines.append(f"Columns      : {list(df_cust.columns)}")
    report_lines.append("\nData Types:")
    for col, dtype in df_cust.dtypes.items():
        report_lines.append(f"  - {col}: {dtype}")

    report_lines.append("\nMissing Values:")
    missing_cust = df_cust.isnull().sum()
    for col, val in missing_cust.items():
        report_lines.append(f"  - {col}: {val} missing ({val / len(df_cust) * 100:.1f}%)")

    cust_dup_count = df_cust.duplicated(subset=['customer_id']).sum()
    report_lines.append(f"\nDuplicate Customer IDs: {cust_dup_count}")

    # Check suspicious email formats
    invalid_emails = df_cust['email'].apply(lambda x: not is_valid_email(x) if pd.notnull(x) else False).sum()
    report_lines.append(f"Invalid Email Formats: {invalid_emails}")

    # Check unparseable signup dates
    invalid_cust_dates = 0
    for dt_val in df_cust['signup_date'].dropna():
        try:
            pd.to_datetime(dt_val, format='mixed')
        except Exception:
            invalid_cust_dates += 1
    report_lines.append(f"Invalid/Unparseable Signup Dates: {invalid_cust_dates}")

    # 2. Profile Transactions
    if not os.path.exists(transactions_path):
        raise FileNotFoundError(f"Transactions raw file not found at {transactions_path}")

    with open(transactions_path, "r", encoding="utf-8") as f:
        txns_raw = json.load(f)

    df_txn = pd.DataFrame(txns_raw)
    report_lines.append("\n--- RAW TRANSACTIONS DATASET ---")
    report_lines.append(f"Row count    : {len(df_txn)}")
    report_lines.append(f"Column count : {len(df_txn.columns)}")
    report_lines.append(f"Columns      : {list(df_txn.columns)}")
    report_lines.append("\nData Types:")
    for col, dtype in df_txn.dtypes.items():
        report_lines.append(f"  - {col}: {dtype}")

    report_lines.append("\nMissing Values:")
    missing_txn = df_txn.isnull().sum()
    for col, val in missing_txn.items():
        report_lines.append(f"  - {col}: {val} missing ({val / len(df_txn) * 100:.1f}%)")

    txn_dup_count = df_txn.duplicated(subset=['transaction_id']).sum()
    report_lines.append(f"\nDuplicate Transaction IDs: {txn_dup_count}")

    # Inspect suspicious numeric quantities & prices
    suspicious_qty = 0
    for q in df_txn['quantity']:
        try:
            val = float(re.sub(r'[^\d.-]', '', str(q))) if pd.notnull(q) else 0
            if val <= 0:
                suspicious_qty += 1
        except Exception:
            suspicious_qty += 1

    suspicious_price = 0
    for p in df_txn['unit_price']:
        if pd.isnull(p):
            suspicious_price += 1
            continue
        try:
            val = float(re.sub(r'[^\d.-]', '', str(p)))
            if val <= 0:
                suspicious_price += 1
        except Exception:
            suspicious_price += 1

    report_lines.append(f"Zero / Negative / Invalid Quantities: {suspicious_qty}")
    report_lines.append(f"Missing / Negative / Invalid Unit Prices: {suspicious_price}")

    # Check orphan transaction records (Customer ID missing in Customer table)
    known_cust_ids = set(df_cust['customer_id'].dropna().astype(str).str.strip())
    txn_cust_ids = df_txn['customer_id'].astype(str).str.strip()
    orphaned_txns = df_txn[~txn_cust_ids.isin(known_cust_ids)]
    report_lines.append(f"Orphaned Transactions (Customer ID missing in Customer table): {len(orphaned_txns)}")

    # 3. Create Quality Breakdown Summary Table (CSV)
    quality_summary = [
        {"dataset": "customers", "metric": "total_records", "count": len(df_cust)},
        {"dataset": "customers", "metric": "duplicate_customer_ids", "count": cust_dup_count},
        {"dataset": "customers", "metric": "missing_email_records", "count": df_cust['email'].isnull().sum()},
        {"dataset": "customers", "metric": "invalid_email_format_records", "count": invalid_emails},
        {"dataset": "customers", "metric": "missing_phone_records", "count": df_cust['phone'].isnull().sum()},
        {"dataset": "customers", "metric": "missing_city_records", "count": df_cust['city'].isnull().sum()},
        {"dataset": "transactions", "metric": "total_records", "count": len(df_txn)},
        {"dataset": "transactions", "metric": "duplicate_transaction_ids", "count": txn_dup_count},
        {"dataset": "transactions", "metric": "invalid_or_negative_quantities", "count": suspicious_qty},
        {"dataset": "transactions", "metric": "invalid_or_missing_prices", "count": suspicious_price},
        {"dataset": "transactions", "metric": "orphaned_referential_key_records", "count": len(orphaned_txns)}
    ]
    df_quality = pd.DataFrame(quality_summary)
    quality_report_csv = os.path.join(output_dir, "data_quality_report.csv")
    df_quality.to_csv(quality_report_csv, index=False)

    txt_report_path = os.path.join(output_dir, "profiling_report.txt")
    report_text = "\n".join(report_lines)
    with open(txt_report_path, "w", encoding="utf-8") as f:
        f.write(report_text)

    print(report_text)
    print(f"\nProfiling completed. Summary saved to {txt_report_path} and {quality_report_csv}")
    
    return {
        "customers_count": len(df_cust),
        "transactions_count": len(df_txn),
        "cust_duplicates": cust_dup_count,
        "txn_duplicates": txn_dup_count,
        "orphaned_transactions": len(orphaned_txns)
    }


if __name__ == "__main__":
    profile_raw_data()
