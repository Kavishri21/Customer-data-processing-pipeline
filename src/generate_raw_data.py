"""
Raw Data Generator for Customer Data Processing & Analytics Pipeline

Generates realistic raw datasets:
- data/raw/customers.csv (~180 records)
- data/raw/transactions.json (~700 records)

Includes realistic data quality issues intentionally for the ETL cleaning & validation pipeline to process.
"""

import json
import random
from datetime import datetime, timedelta
import pandas as pd
import numpy as np


def generate_customers():
    random.seed(42)
    np.random.seed(42)

    first_names = [
        "Aarav", "Ananya", "Rohan", "Priya", "Rahul", "Sneha", "Vikram", "Neha",
        "Aditya", "Kavya", "Siddharth", "Pooja", "Amit", "Divya", "Karan", "Riya",
        "Arjun", "Ishita", "Varun", "Meera", "Suresh", "Anita", "Rajesh", "Sunita",
        "Deepak", "Aarti", "Manish", "Swati", "Sanjay", "Rekha", "Nikhil", "Shweta"
    ]
    
    last_names = [
        "Sharma", "Verma", "Patel", "Gupta", "Kumar", "Singh", "Reddy", "Nair",
        "Joshi", "Rao", "Iyer", "Mehta", "Shah", "Agarwal", "Chawla", "Deshmukh",
        "Kulkarni", "Banerjee", "Chatterjee", "Pillai", "Bhat", "Saxena", "Kapoor"
    ]

    cities_dirty = [
        "Chennai", "chennai", "CHENNAI", " Chennai ", "Chennai",
        "Mumbai", "mumbai", "MUMBAI", " Mumbai",
        "Bengaluru", "bengaluru", "Bangalore", "BENGALURU ",
        "Delhi", "delhi", "New Delhi", "DELHI",
        "Hyderabad", "hyderabad", "HYDERABAD",
        "Pune", "pune", "PUNE",
        "Kolkata", "kolkata",
        "Ahmedabad", "ahmedabad"
    ]

    states = ["Tamil Nadu", "Maharashtra", "Karnataka", "Delhi", "Telangana", "West Bengal", "Gujarat"]

    segments = ["Consumer", "Corporate", "Home Office", "consumer", "CORPORATE", "  Consumer  "]

    customers = []
    
    # 150 unique valid customer IDs (CUST-1001 to CUST-1150)
    for i in range(1, 151):
        cust_id = f"CUST-{1000 + i}"
        fn = random.choice(first_names)
        ln = random.choice(last_names)
        name = f"  {fn} {ln}  " if i % 7 == 0 else f"{fn} {ln}"
        
        # Introduce invalid email formats
        if i % 15 == 0:
            email = None  # Missing
        elif i % 13 == 0:
            email = f"{fn.lower()}.{ln.lower()}gmail.com"  # Missing @
        elif i % 11 == 0:
            email = f"{fn.lower()}@@domain..com"  # Malformed
        elif i % 9 == 0:
            email = f"{fn.lower()}{ln.lower()}@domain"  # Missing TLD
        else:
            email = f"{fn.lower()}.{ln.lower()}{i}@example.com"

        # Introduce missing / malformed phone numbers
        if i % 12 == 0:
            phone = None
        elif i % 8 == 0:
            phone = f"+91-{random.randint(7000000000, 9999999999)}"
        else:
            phone = f"{random.randint(7000000000, 9999999999)}"

        # Inconsistent city
        city = None if i % 17 == 0 else random.choice(cities_dirty)
        state = random.choice(states)

        # Inconsistent dates
        signup_dt = datetime(2022, 1, 1) + timedelta(days=random.randint(0, 700))
        if i % 14 == 0:
            signup_date = signup_dt.strftime("%d/%m/%Y")
        elif i % 10 == 0:
            signup_date = signup_dt.strftime("%Y/%m/%d")
        elif i % 25 == 0:
            signup_date = "invalid-date-string"
        else:
            signup_date = signup_dt.strftime("%Y-%m-%d")

        segment = random.choice(segments)

        customers.append({
            "customer_id": cust_id,
            "customer_name": name,
            "email": email,
            "phone": phone,
            "city": city,
            "state": state,
            "signup_date": signup_date,
            "customer_segment": segment
        })

    # Add ~25 duplicate rows (some exact duplicates, some duplicate customer_ids)
    duplicates = random.sample(customers, 20)
    for dup in duplicates:
        dup_copy = dup.copy()
        if random.random() > 0.5:
            dup_copy["customer_name"] = dup_copy["customer_name"].lower()
        customers.append(dup_copy)

    # Add ~5 invalid customer ID rows
    customers.append({
        "customer_id": "INVALID_ID_999",
        "customer_name": "Ghost User",
        "email": "ghost@test.com",
        "phone": "9999999999",
        "city": "Chennai",
        "state": "Tamil Nadu",
        "signup_date": "2023-01-01",
        "customer_segment": "Consumer"
    })
    
    df_customers = pd.DataFrame(customers)
    # Shuffle
    df_customers = df_customers.sample(frac=1, random_state=42).reset_index(drop=True)
    return df_customers


def generate_transactions(valid_customer_ids):
    random.seed(42)
    
    products_by_category = {
        "Electronics": [
            ("Wireless Headphones", 2499.00),
            ("Smart Watch", 4999.00),
            ("Bluetooth Speaker", 1999.00),
            ("USB-C Hub", 1299.00),
            ("Mechanical Keyboard", 3499.00),
            ("Gaming Mouse", 1599.00)
        ],
        "Clothing": [
            ("Cotton T-Shirt", 599.00),
            ("Slim Fit Denim Jeans", 1799.00),
            ("Casual Hooded Sweatshirt", 1499.00),
            ("Formal Dress Shirt", 1299.00),
            ("Sports Running Shoes", 2999.00)
        ],
        "Home & Kitchen": [
            ("Stainless Steel Water Bottle", 499.00),
            ("Electric Coffee Maker", 2299.00),
            ("Air Fryer 4L", 5999.00),
            ("Non-Stick Frying Pan", 899.00),
            ("LED Desk Lamp", 799.00)
        ],
        "Books": [
            ("Data Engineering Essentials", 899.00),
            ("Python Data Analysis Guide", 659.00),
            ("Designing Data-Intensive Applications", 1200.00),
            ("SQL Query Optimization", 750.00)
        ],
        "Beauty": [
            ("Organic Face Wash", 349.00),
            ("Sunscreen SPF 50", 499.00),
            ("Moisturizing Cream", 299.00),
            ("Hair Nourishing Serum", 450.00)
        ]
    }

    category_variations = {
        "Electronics": ["Electronics", "electronics", "ELECTR0NICS", "  Electronics  ", "ELECTRONICS"],
        "Clothing": ["Clothing", "clothing", "CLOTHING", "  Clothing"],
        "Home & Kitchen": ["Home & Kitchen", "home & kitchen", "HOME & KITCHEN", "Home and Kitchen"],
        "Books": ["Books", "books", "BOOKS"],
        "Beauty": ["Beauty", "beauty", "BEAUTY"]
    }

    payment_methods_dirty = [
        "Credit Card", "credit_card", "CREDIT CARD", "CC", " Credit Card ",
        "UPI", "upi", "Upi", "  UPI  ",
        "Debit Card", "debit_card", "DEBIT CARD",
        "Net Banking", "net_banking", "NET BANKING",
        "Cash on Delivery", "COD", "cod", "Cash On Delivery"
    ]

    statuses = ["Completed", "completed", "COMPLETED", "Pending", "pending", "Failed", "failed", "Cancelled"]

    transactions = []
    
    # Generate 650 valid transaction records (TXN-10001 to TXN-10650)
    for i in range(1, 651):
        txn_id = f"TXN-{10000 + i}"
        
        # Introduce orphan customer_ids (referential integrity check issue)
        if i % 25 == 0:
            cust_id = f"CUST-999{i % 5}"  # Customer does NOT exist in customers table!
        else:
            cust_id = random.choice(valid_customer_ids)

        # Date variations
        txn_dt = datetime(2023, 1, 1) + timedelta(days=random.randint(0, 450), hours=random.randint(0, 23), minutes=random.randint(0, 59))
        if i % 18 == 0:
            txn_date = txn_dt.strftime("%d/%m/%Y %H:%M:%S")
        elif i % 22 == 0:
            txn_date = "invalid-timestamp"
        else:
            txn_date = txn_dt.strftime("%Y-%m-%d %H:%M:%S")

        cat_clean = random.choice(list(products_by_category.keys()))
        cat_dirty = random.choice(category_variations[cat_clean])
        prod_name, base_price = random.choice(products_by_category[cat_clean])

        # Quantities & prices with data quality issues
        if i % 30 == 0:
            quantity = -1  # Negative quantity!
        elif i % 40 == 0:
            quantity = 0   # Zero quantity!
        elif i % 16 == 0:
            quantity = f"{random.randint(1, 5)} units"  # String with text
        else:
            quantity = random.randint(1, 5)

        if i % 35 == 0:
            unit_price = None  # Missing price
        elif i % 14 == 0:
            unit_price = f"${base_price:.2f}"  # Price with dollar sign
        elif i % 45 == 0:
            unit_price = -49.99  # Negative price!
        else:
            unit_price = base_price

        payment_method = random.choice(payment_methods_dirty)
        status = random.choice(statuses)

        transactions.append({
            "transaction_id": txn_id,
            "customer_id": cust_id,
            "transaction_date": txn_date,
            "product": prod_name,
            "category": cat_dirty,
            "quantity": quantity,
            "unit_price": unit_price,
            "payment_method": payment_method,
            "transaction_status": status
        })

    # Add ~30 duplicate transaction rows
    dup_txns = random.sample(transactions, 30)
    for dup in dup_txns:
        transactions.append(dup.copy())

    # Shuffle
    random.shuffle(transactions)
    return transactions


def main():
    print("Generating raw customers.csv dataset...")
    df_customers = generate_customers()
    valid_customer_ids = [cid for cid in df_customers['customer_id'].unique() if cid.startswith("CUST-")]
    
    customers_path = "data/raw/customers.csv"
    df_customers.to_csv(customers_path, index=False)
    print(f"Saved {len(df_customers)} customer records to {customers_path}")

    print("Generating raw transactions.json dataset...")
    transactions = generate_transactions(valid_customer_ids)
    
    transactions_path = "data/raw/transactions.json"
    with open(transactions_path, "w", encoding="utf-8") as f:
        json.dump(transactions, f, indent=2)
    print(f"Saved {len(transactions)} transaction records to {transactions_path}")


if __name__ == "__main__":
    main()
