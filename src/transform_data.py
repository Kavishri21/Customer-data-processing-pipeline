"""
Data Transformation Module for Customer Data Processing & Analytics Pipeline

Applies business logic and features engineering to clean datasets:
- Total amount calculation (quantity * unit_price)
- Date dimension extractions (year, month, month_name)
- Customer tenure calculation (signup_date to reference date)
- Per-customer transactional summary aggregates (total spend, order count, AOV)
"""

import os
import pandas as pd
from datetime import datetime


def transform_data(cust_path="data/processed/customers_clean.csv",
                   txn_path="data/processed/transactions_clean.csv"):
    """
    Transforms clean datasets by computing derived columns and aggregations.
    """
    print("Executing Data Transformation Stage...")
    
    if not os.path.exists(cust_path) or not os.path.exists(txn_path):
        raise FileNotFoundError("Clean datasets not found. Please run clean_data.py first.")

    df_cust = pd.read_csv(cust_path)
    df_txn = pd.read_csv(txn_path)

    # 1. Customer Transformations
    # Convert signup_date to datetime
    signup_dt = pd.to_datetime(df_cust['signup_date'])
    ref_date = datetime(2026, 10, 1)  # Pipeline reference date
    
    # Customer tenure in days
    df_cust['customer_tenure_days'] = (ref_date - signup_dt).dt.days
    # Enforce minimum tenure of 0 days
    df_cust['customer_tenure_days'] = df_cust['customer_tenure_days'].apply(lambda x: max(x, 0))

    # 2. Transaction Transformations
    # Calculated Column: total_amount = quantity * unit_price
    df_txn['total_amount'] = (df_txn['quantity'] * df_txn['unit_price']).round(2)

    # Date extractions
    txn_dt = pd.to_datetime(df_txn['transaction_date'])
    df_txn['transaction_year'] = txn_dt.dt.year
    df_txn['transaction_month'] = txn_dt.dt.month
    df_txn['transaction_month_name'] = txn_dt.dt.strftime('%b')

    # 3. Demonstration of Merge and Aggregation
    # Group by customer_id to calculate customer-level metrics
    customer_stats = df_txn[df_txn['transaction_status'] == 'Completed'].groupby('customer_id').agg(
        total_spent=('total_amount', 'sum'),
        total_completed_orders=('transaction_id', 'count'),
        avg_order_value=('total_amount', 'mean')
    ).reset_index()

    customer_stats['total_spent'] = customer_stats['total_spent'].round(2)
    customer_stats['avg_order_value'] = customer_stats['avg_order_value'].round(2)

    # Merge stats back with customer DataFrame (demonstrates LEFT JOIN in Pandas)
    df_cust_enriched = pd.merge(df_cust, customer_stats, on='customer_id', how='left')
    df_cust_enriched['total_spent'] = df_cust_enriched['total_spent'].fillna(0.0)
    df_cust_enriched['total_completed_orders'] = df_cust_enriched['total_completed_orders'].fillna(0).astype(int)
    df_cust_enriched['avg_order_value'] = df_cust_enriched['avg_order_value'].fillna(0.0)

    # Re-save updated clean datasets
    df_cust.to_csv(cust_path, index=False)
    df_txn.to_csv(txn_path, index=False)

    print(f"Transformed Customer Dataset: Added 'customer_tenure_days' ({len(df_cust)} records)")
    print(f"Transformed Transaction Dataset: Added 'total_amount', 'transaction_year', 'transaction_month' ({len(df_txn)} records)")
    
    return {
        "customers_transformed": len(df_cust),
        "transactions_transformed": len(df_txn),
        "total_calculated_revenue": float(df_txn[df_txn['transaction_status'] == 'Completed']['total_amount'].sum())
    }


if __name__ == "__main__":
    transform_data()
