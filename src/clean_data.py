"""
Data Cleaning Module for Customer Data Processing & Analytics Pipeline

Handles:
- Missing value imputation with documented strategy decisions
- De-duplication of customer and transaction records
- Text normalization (casing, whitespace trimming, standardized categories & payment methods)
- Email validation using regex
- Date parsing and formatting
- Numeric parsing (stripping currency symbols/units, enforcing positive quantities & prices)
- Referential integrity validation (routing orphaned/invalid records to invalid_transactions.csv)
"""

import os
import re
import json
import pandas as pd
import numpy as np


def is_valid_email(email):
    """Checks if email string matches standard RFC pattern."""
    if not isinstance(email, str) or not email.strip():
        return False
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(pattern, email.strip()))


def clean_text_field(val):
    """Strips leading/trailing whitespace from string fields."""
    if pd.isnull(val):
        return val
    val_str = str(val).strip()
    return val_str if val_str else None


def clean_customers(df_cust):
    """
    Cleans raw customer DataFrame.
    
    Cleaning Strategy:
    1. Filter out invalid customer ID records (e.g., 'INVALID_ID_999').
    2. Strip whitespace across string columns.
    3. Normalize Customer Name: Title case.
    4. Email Validation: Set invalid email formats to NULL (NaN) to prevent bad data in DB.
    5. Missing Phone: Impute missing values as 'Unknown' (non-critical contact field).
    6. City Standardization: Map variations (e.g. 'chennai', 'CHENNAI', 'Bangalore') to standard names.
    7. Missing City / State: Impute missing values as 'Unknown'.
    8. Date Cleaning: Coerce signup_date to datetime; drop records with completely corrupt dates.
    9. Customer Segment Standardization: Map casing variations ('consumer', 'CORPORATE') to standard 'Consumer', 'Corporate', 'Home Office'.
    10. Deduplication: Keep first occurrence of unique customer_id.
    """
    df = df_cust.copy()

    # 1. Filter out malformed customer_id strings
    df = df[df['customer_id'].astype(str).str.startswith("CUST-")].copy()

    # 2. Strip whitespace from text fields
    text_cols = ['customer_id', 'customer_name', 'email', 'phone', 'city', 'state', 'customer_segment']
    for col in text_cols:
        if col in df.columns:
            df[col] = df[col].apply(clean_text_field)

    # 3. Normalize Customer Name
    df['customer_name'] = df['customer_name'].apply(lambda x: x.title() if pd.notnull(x) else "Unknown Customer")

    # 4. Email validation
    df['email'] = df['email'].apply(lambda x: x.lower() if is_valid_email(x) else None)

    # 5. Missing Phone Imputation
    df['phone'] = df['phone'].fillna("Unknown")

    # 6. City & State Normalization
    city_mapping = {
        "chennai": "Chennai", "CHENNAI": "Chennai", " Chennai ": "Chennai",
        "mumbai": "Mumbai", "MUMBAI": "Mumbai",
        "bengaluru": "Bengaluru", "bengaluru ": "Bengaluru", "Bangalore": "Bengaluru", "BENGALURU ": "Bengaluru",
        "delhi": "Delhi", "DELHI": "Delhi", "New Delhi": "Delhi",
        "hyderabad": "Hyderabad", "HYDERABAD": "Hyderabad",
        "pune": "Pune", "PUNE": "Pune",
        "kolkata": "Kolkata", "ahmedabad": "Ahmedabad"
    }
    df['city'] = df['city'].apply(lambda x: city_mapping.get(x, x.title()) if pd.notnull(x) else "Unknown")
    df['state'] = df['state'].apply(lambda x: x.title() if pd.notnull(x) else "Unknown")

    # 7. Customer Segment Standardization
    segment_mapping = {
        "consumer": "Consumer", "CONSUMER": "Consumer",
        "corporate": "Corporate", "CORPORATE": "Corporate",
        "home office": "Home Office", "HOME OFFICE": "Home Office"
    }
    df['customer_segment'] = df['customer_segment'].apply(
        lambda x: segment_mapping.get(str(x).lower().strip(), "Consumer") if pd.notnull(x) else "Consumer"
    )

    # 8. Date Parsing
    df['signup_date'] = pd.to_datetime(df['signup_date'], format='mixed', errors='coerce')
    # Drop rows with unparseable signup dates
    df = df.dropna(subset=['signup_date']).copy()
    df['signup_date'] = df['signup_date'].dt.strftime('%Y-%m-%d')

    # 9. Deduplication
    df = df.drop_duplicates(subset=['customer_id'], keep='first').copy()

    return df


def parse_numeric_quantity(val):
    """Extracts integer quantity from mixed text/numeric representation."""
    if pd.isnull(val):
        return None
    try:
        val_str = str(val)
        num_part = re.sub(r'[^\d.-]', '', val_str)
        if not num_part:
            return None
        qty = int(float(num_part))
        return qty if qty > 0 else None
    except Exception:
        return None


def parse_numeric_price(val):
    """Extracts float price from currency formatted string ($199.99 or INR 450)."""
    if pd.isnull(val):
        return None
    try:
        val_str = str(val)
        num_part = re.sub(r'[^\d.-]', '', val_str)
        if not num_part:
            return None
        price = float(num_part)
        return round(price, 2) if price > 0 else None
    except Exception:
        return None


def clean_transactions(df_txn, valid_customer_ids):
    """
    Cleans raw transaction DataFrame and separates invalid/orphaned records.
    
    Cleaning Strategy:
    1. Trim whitespace on text columns.
    2. Category Standardization: Map casing variations to standard names.
    3. Payment Method Standardization: Map variations ('CC', 'credit_card', 'upi') to standard names.
    4. Transaction Status Normalization: Map ('completed', 'PENDING') to Title case.
    5. Quantity & Price Cleaning: Parse numbers, reject zero or negative values.
    6. Date Parsing: Coerce transaction_date to datetime format.
    7. Deduplication: Remove duplicate transaction_id records.
    8. Referential Integrity Check: Verify customer_id exists in clean customers dataset.
    """
    df = df_txn.copy()

    # 1. Trim whitespace
    text_cols = ['transaction_id', 'customer_id', 'product', 'category', 'payment_method', 'transaction_status']
    for col in text_cols:
        if col in df.columns:
            df[col] = df[col].apply(clean_text_field)

    # 2. Category Normalization
    cat_mapping = {
        "electronics": "Electronics", "electr0nics": "Electronics", "electronics  ": "Electronics",
        "clothing": "Clothing",
        "home & kitchen": "Home & Kitchen", "home and kitchen": "Home & Kitchen",
        "books": "Books",
        "beauty": "Beauty"
    }
    df['category'] = df['category'].apply(
        lambda x: cat_mapping.get(str(x).lower().strip(), str(x).strip().title()) if pd.notnull(x) else "General"
    )

    # 3. Payment Method Normalization
    pm_mapping = {
        "credit card": "Credit Card", "credit_card": "Credit Card", "cc": "Credit Card",
        "upi": "UPI",
        "debit card": "Debit Card", "debit_card": "Debit Card",
        "net banking": "Net Banking", "net_banking": "Net Banking",
        "cash on delivery": "Cash on Delivery", "cod": "Cash on Delivery"
    }
    df['payment_method'] = df['payment_method'].apply(
        lambda x: pm_mapping.get(str(x).lower().strip(), str(x).strip().title()) if pd.notnull(x) else "Unknown"
    )

    # 4. Status Normalization
    status_mapping = {
        "completed": "Completed",
        "pending": "Pending",
        "failed": "Failed",
        "cancelled": "Cancelled"
    }
    df['transaction_status'] = df['transaction_status'].apply(
        lambda x: status_mapping.get(str(x).lower().strip(), "Completed") if pd.notnull(x) else "Completed"
    )

    # 5. Numeric Cleaning
    df['clean_quantity'] = df['quantity'].apply(parse_numeric_quantity)
    df['clean_unit_price'] = df['unit_price'].apply(parse_numeric_price)

    # 6. Date Parsing
    df['clean_date'] = pd.to_datetime(df['transaction_date'], format='mixed', errors='coerce')

    # 7. Deduplication by transaction_id
    df = df.drop_duplicates(subset=['transaction_id'], keep='first').copy()

    # 8. Referential Integrity & Validity Check
    invalid_mask = (
        df['clean_quantity'].isnull() |
        df['clean_unit_price'].isnull() |
        df['clean_date'].isnull() |
        (~df['customer_id'].isin(valid_customer_ids))
    )

    # Separate into invalid vs clean records
    df_invalid = df[invalid_mask].copy()
    
    # Annotate invalid reason for transparency
    reasons = []
    for idx, row in df_invalid.iterrows():
        r = []
        if pd.isnull(row['clean_quantity']):
            r.append("Invalid or non-positive quantity")
        if pd.isnull(row['clean_unit_price']):
            r.append("Invalid or non-positive unit_price")
        if pd.isnull(row['clean_date']):
            r.append("Invalid or unparseable transaction_date")
        if row['customer_id'] not in valid_customer_ids:
            r.append(f"Orphaned customer_id ({row['customer_id']} not found in customers table)")
        reasons.append("; ".join(r))
    df_invalid['rejection_reason'] = reasons

    # Clean subset
    df_clean = df[~invalid_mask].copy()
    df_clean['quantity'] = df_clean['clean_quantity'].astype(int)
    df_clean['unit_price'] = df_clean['clean_unit_price'].astype(float)
    df_clean['transaction_date'] = df_clean['clean_date'].dt.strftime('%Y-%m-%d %H:%M:%S')

    # Drop temporary clean columns
    df_clean = df_clean.drop(columns=['clean_quantity', 'clean_unit_price', 'clean_date'])

    return df_clean, df_invalid


def run_cleaning_pipeline(raw_cust_path="data/raw/customers.csv",
                          raw_txn_path="data/raw/transactions.json",
                          processed_dir="data/processed"):
    """Runs the full cleaning pipeline and saves clean data and invalid records."""
    os.makedirs(processed_dir, exist_ok=True)

    print("Executing Data Cleaning Stage...")
    df_raw_cust = pd.read_csv(raw_cust_path)
    df_clean_cust = clean_customers(df_raw_cust)

    valid_cust_ids = set(df_clean_cust['customer_id'].unique())

    with open(raw_txn_path, "r", encoding="utf-8") as f:
        txns_raw = json.load(f)
    df_raw_txn = pd.DataFrame(txns_raw)

    df_clean_txn, df_invalid_txn = clean_transactions(df_raw_txn, valid_cust_ids)

    # Save outputs
    clean_cust_path = os.path.join(processed_dir, "customers_clean.csv")
    clean_txn_path = os.path.join(processed_dir, "transactions_clean.csv")
    invalid_txn_path = os.path.join(processed_dir, "invalid_transactions.csv")

    df_clean_cust.to_csv(clean_cust_path, index=False)
    df_clean_txn.to_csv(clean_txn_path, index=False)
    
    # Save selected columns for invalid transactions
    invalid_cols = ['transaction_id', 'customer_id', 'transaction_date', 'product', 'quantity', 'unit_price', 'rejection_reason']
    avail_cols = [c for c in invalid_cols if c in df_invalid_txn.columns]
    df_invalid_txn[avail_cols].to_csv(invalid_txn_path, index=False)

    print(f"Clean Customers saved to {clean_cust_path} ({len(df_clean_cust)} records)")
    print(f"Clean Transactions saved to {clean_txn_path} ({len(df_clean_txn)} records)")
    print(f"Invalid Transactions isolated in {invalid_txn_path} ({len(df_invalid_txn)} records)")

    return {
        "raw_customers_count": len(df_raw_cust),
        "clean_customers_count": len(df_clean_cust),
        "raw_transactions_count": len(df_raw_txn),
        "clean_transactions_count": len(df_clean_txn),
        "invalid_transactions_count": len(df_invalid_txn)
    }


if __name__ == "__main__":
    run_cleaning_pipeline()
