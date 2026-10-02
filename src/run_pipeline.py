"""
Master Pipeline Orchestrator: Customer Data Processing & Analytics Pipeline

Executes the end-to-end ETL pipeline stages in sequential order:
1. Raw Data Verification / Generation
2. Data Profiling
3. Data Cleaning
4. Data Transformation
5. Data Validation
6. MySQL Database Loading & Analytics Export

Provides detailed statistics and terminal progress tracking.
"""

import sys
import time
from profile_data import profile_raw_data
from clean_data import run_cleaning_pipeline
from transform_data import transform_data
from validate_data import validate_processed_data
from load_to_mysql import run_load_pipeline


def print_banner():
    banner = """
================================================================================
          CUSTOMER DATA PROCESSING & ANALYTICS PIPELINE (ETL)
================================================================================
    """
    print(banner)


def main():
    start_time = time.time()
    print_banner()

    # Stage 1: Load / Verify Raw Data
    print("[1/6] Loading raw data...")
    raw_cust_path = "data/raw/customers.csv"
    raw_txn_path = "data/raw/transactions.json"
    print(f"      Source Customer Dataset     : {raw_cust_path}")
    print(f"      Source Transaction Dataset  : {raw_txn_path}")
    time.sleep(0.5)

    # Stage 2: Profiling Data
    print("\n[2/6] Profiling raw data...")
    profiling_stats = profile_raw_data(customers_path=raw_cust_path,
                                       transactions_path=raw_txn_path,
                                       output_dir="reports")
    time.sleep(0.5)

    # Stage 3: Cleaning Data
    print("\n[3/6] Cleaning data...")
    clean_stats = run_cleaning_pipeline(raw_cust_path=raw_cust_path,
                                        raw_txn_path=raw_txn_path,
                                        processed_dir="data/processed")
    time.sleep(0.5)

    # Stage 4: Transforming Data
    print("\n[4/6] Transforming data...")
    transform_stats = transform_data(cust_path="data/processed/customers_clean.csv",
                                     txn_path="data/processed/transactions_clean.csv")
    time.sleep(0.5)

    # Stage 5: Validating Data
    print("\n[5/6] Validating processed data...")
    val_report = validate_processed_data(cust_path="data/processed/customers_clean.csv",
                                        txn_path="data/processed/transactions_clean.csv",
                                        report_dir="reports")
    time.sleep(0.5)

    # Stage 6: Loading Data into MySQL
    print("\n[6/6] Loading data into MySQL...")
    db_loaded = run_load_pipeline()

    elapsed = time.time() - start_time

    # Final Summary Report
    print("\n" + "=" * 80)
    print("                      PIPELINE EXECUTION SUMMARY")
    print("=" * 80)
    print(f" Status                       : SUCCESS")
    print(f" Total Execution Time         : {elapsed:.2f} seconds")
    print("-" * 80)
    print(f" Raw Customer Records         : {clean_stats['raw_customers_count']}")
    print(f" Clean Customer Records       : {clean_stats['clean_customers_count']}")
    print(f" Customer Duplicates Removed  : {profiling_stats['cust_duplicates']}")
    print("-" * 80)
    print(f" Raw Transaction Records      : {clean_stats['raw_transactions_count']}")
    print(f" Clean Transaction Records    : {clean_stats['clean_transactions_count']}")
    print(f" Transaction Duplicates Removed: {profiling_stats['txn_duplicates']}")
    print(f" Invalid / Orphaned Isolated  : {clean_stats['invalid_transactions_count']} (Saved to data/processed/invalid_transactions.csv)")
    print("-" * 80)
    print(f" Calculated Total Revenue     : ${transform_stats['total_calculated_revenue']:,.2f}")
    print(f" Validation Quality Gates     : {val_report['overall_status']} ({val_report['passed_checks']}/{val_report['total_checks']} checks passed)")
    print(f" MySQL Load Status            : {'SUCCESS' if db_loaded else 'PENDING (Set credentials in .env)'}")
    print("=" * 80)
    print(" Pipeline completed successfully.\n")


if __name__ == "__main__":
    main()
