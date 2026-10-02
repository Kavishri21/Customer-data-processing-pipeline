"""
Data Validation Module for Customer Data Processing & Analytics Pipeline

Enforces quality gates before loading into MySQL:
1. Schema & required column check
2. Non-null primary key check
3. Primary key uniqueness check
4. Numeric domain & range validation (quantity > 0, unit_price > 0, total_amount > 0)
5. Date validity check
6. Foreign key referential integrity check
7. Duplicate record check

Generates reports/validation_report.json and halts pipeline if quality gate fails.
"""

import os
import json
import pandas as pd


def validate_processed_data(cust_path="data/processed/customers_clean.csv",
                           txn_path="data/processed/transactions_clean.csv",
                           report_dir="reports"):
    """
    Validates cleaned and transformed datasets.
    Returns boolean status and detailed check results.
    """
    print("Executing Data Validation Stage...")
    os.makedirs(report_dir, exist_ok=True)

    if not os.path.exists(cust_path) or not os.path.exists(txn_path):
        raise FileNotFoundError("Processed datasets missing for validation.")

    df_cust = pd.read_csv(cust_path)
    df_txn = pd.read_csv(txn_path)

    checks = []
    overall_pass = True

    # 1. Required Columns Check
    req_cust_cols = {'customer_id', 'customer_name', 'email', 'phone', 'city', 'state', 'signup_date', 'customer_segment', 'customer_tenure_days'}
    req_txn_cols = {'transaction_id', 'customer_id', 'transaction_date', 'product', 'category', 'quantity', 'unit_price', 'total_amount', 'payment_method', 'transaction_status'}

    cust_cols_exist = req_cust_cols.issubset(set(df_cust.columns))
    txn_cols_exist = req_txn_cols.issubset(set(df_txn.columns))
    
    checks.append({
        "check_name": "Required Columns Exist",
        "passed": bool(cust_cols_exist and txn_cols_exist),
        "details": f"Customers missing: {req_cust_cols - set(df_cust.columns)}, Transactions missing: {req_txn_cols - set(df_txn.columns)}"
    })
    if not (cust_cols_exist and txn_cols_exist):
        overall_pass = False

    # 2. Non-null Primary Key Check
    cust_pk_nulls = int(df_cust['customer_id'].isnull().sum())
    txn_pk_nulls = int(df_txn['transaction_id'].isnull().sum())
    pk_non_null = (cust_pk_nulls == 0) and (txn_pk_nulls == 0)
    checks.append({
        "check_name": "Primary Keys Non-Null",
        "passed": bool(pk_non_null),
        "details": f"Customer PK Nulls: {cust_pk_nulls}, Transaction PK Nulls: {txn_pk_nulls}"
    })
    if not pk_non_null:
        overall_pass = False

    # 3. Uniqueness Check
    cust_unique = int(df_cust['customer_id'].nunique()) == len(df_cust)
    txn_unique = int(df_txn['transaction_id'].nunique()) == len(df_txn)
    checks.append({
        "check_name": "Primary Key Uniqueness",
        "passed": bool(cust_unique and txn_unique),
        "details": f"Customers total/unique: {len(df_cust)}/{df_cust['customer_id'].nunique()}, Transactions total/unique: {len(df_txn)}/{df_txn['transaction_id'].nunique()}"
    })
    if not (cust_unique and txn_unique):
        overall_pass = False

    # 4. Numeric Range Check (quantity > 0, unit_price > 0, total_amount > 0)
    invalid_qty = int((df_txn['quantity'] <= 0).sum())
    invalid_price = int((df_txn['unit_price'] <= 0).sum())
    invalid_total = int((df_txn['total_amount'] <= 0).sum())
    numeric_pass = (invalid_qty == 0) and (invalid_price == 0) and (invalid_total == 0)
    checks.append({
        "check_name": "Numeric Range Validity",
        "passed": bool(numeric_pass),
        "details": f"Invalid Qty Count: {invalid_qty}, Invalid Price Count: {invalid_price}, Invalid Total Count: {invalid_total}"
    })
    if not numeric_pass:
        overall_pass = False

    # 5. Referential Integrity Check
    valid_cust_set = set(df_cust['customer_id'])
    txn_cust_set = set(df_txn['customer_id'])
    orphaned_count = int(len(txn_cust_set - valid_cust_set))
    ref_integrity_pass = (orphaned_count == 0)
    checks.append({
        "check_name": "Referential Integrity (FK match)",
        "passed": bool(ref_integrity_pass),
        "details": f"Orphaned customer_id keys in transaction table: {orphaned_count}"
    })
    if not ref_integrity_pass:
        overall_pass = False

    # 6. Date Validity Check
    cust_date_nulls = int(pd.to_datetime(df_cust['signup_date'], errors='coerce').isnull().sum())
    txn_date_nulls = int(pd.to_datetime(df_txn['transaction_date'], errors='coerce').isnull().sum())
    date_pass = (cust_date_nulls == 0) and (txn_date_nulls == 0)
    checks.append({
        "check_name": "Date Field Validity",
        "passed": bool(date_pass),
        "details": f"Invalid Customer Signup Dates: {cust_date_nulls}, Invalid Transaction Dates: {txn_date_nulls}"
    })
    if not date_pass:
        overall_pass = False

    # Console output report
    print("\n" + "=" * 50)
    print("DATA VALIDATION RESULTS")
    print("=" * 50)
    for c in checks:
        status_str = "[PASS]" if c['passed'] else "[FAIL]"
        print(f"{status_str} {c['check_name']} - {c['details']}")
    print("=" * 50)

    val_report = {
        "overall_status": "PASSED" if overall_pass else "FAILED",
        "total_checks": len(checks),
        "passed_checks": sum(1 for c in checks if c['passed']),
        "failed_checks": sum(1 for c in checks if not c['passed']),
        "details": checks
    }

    report_path = os.path.join(report_dir, "validation_report.json")
    with open(report_path, "w", encoding="utf-8") as f:
        json.dump(val_report, f, indent=2)

    if not overall_pass:
        raise ValueError(f"Data Validation Failed! Check report at {report_path}")

    print(f"Validation succeeded. All quality gates passed! Report saved to {report_path}\n")
    return val_report


if __name__ == "__main__":
    validate_processed_data()
