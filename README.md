# Customer Data Processing & Analytics Pipeline (ETL)

A modular, production-style **Batch Data Engineering Pipeline** built with Python, Pandas, MySQL, and SQL. 

This project ingests semi-structured customer demographics and transaction logs, profiles raw data quality issues, cleans and standardizes records, enforces validation quality gates, loads clean data into a MySQL relational database, and executes SQL analytics queries for business reporting.

---

## 🏗️ Architecture

```text
Raw Data (CSV & JSON) 
   │
   ▼
[1] Data Profiling (profile_data.py) ➔ Identifies nulls, duplicates, invalid formats & orphaned keys
   │
   ▼
[2] Data Cleaning (clean_data.py)    ➔ Text/email normalization, imputation, isolates invalid records
   │
   ▼
[3] Transformation (transform_data.py)➔ Computes line totals, date dimensions & tenure metrics
   │
   ▼
[4] Quality Gate (validate_data.py)  ➔ Validates PK uniqueness, FK referential integrity & ranges
   │
   ▼
[5] Database Load (load_to_mysql.py)  ➔ Bulk batch insertion into MySQL database
   │
   ▼
[6] SQL Analytics (sql/analytics.sql) ➔ 15 analytical queries for business insights
```

---

## 📁 Repository Structure

```text
customer-data-processing-pipeline/
├── data/
│   ├── raw/                  # Source CSV & JSON files
│   └── processed/            # Cleaned data & isolated invalid records
├── src/
│   ├── generate_raw_data.py  # Synthetic raw dataset generator
│   ├── profile_data.py       # Profiling & quality metrics
│   ├── clean_data.py         # Cleaning & deduplication pipeline
│   ├── transform_data.py     # Feature engineering & derived metrics
│   ├── validate_data.py      # Assertion validation gate
│   ├── load_to_mysql.py      # MySQL connector & batch loader
│   └── run_pipeline.py       # Master pipeline orchestrator
├── sql/
│   ├── schema.sql            # DDL script creating database, tables & indexes
│   └── analytics.sql         # 15 analytical SQL queries
├── reports/                  # Profiling, validation & analytics outputs
├── .env.example              # Template for database credentials
├── .gitignore                # Git exclusion rules
├── requirements.txt          # Python dependencies
└── README.md                 # Project documentation
```

---

## 🛠️ Pipeline Stages

1. **Extract & Profile**: Scans raw datasets (`customers.csv`, `transactions.json`) to detect missing values, invalid email formats, unparseable dates, negative prices/quantities, duplicate IDs, and orphaned transaction keys.
2. **Clean & Isolate**: Normalizes text casing (e.g. `'chennai'` $\rightarrow$ `'Chennai'`), validates emails via regex (invalid emails set to `NULL`), imputes missing phone numbers as `'Unknown'`, and routes invalid/orphaned transactions to `invalid_transactions.csv`.
3. **Transform**: Computes line totals (`total_amount = quantity * unit_price`), extracts year/month dimensions, and calculates `customer_tenure_days`.
4. **Validate Gate**: Enforces quality assertions (non-null PKs, PK uniqueness, positive ranges, FK match) before database insertion.
5. **MySQL Load**: Initializes database schema (`sql/schema.sql`) with primary keys, foreign keys (`ON DELETE CASCADE`), and performance B-Tree indexes, then performs bulk batch insertion.
6. **SQL Analytics**: Runs 15 SQL queries covering revenue trends, top customer spenders, product category performance, and inactive user pools.

---

## 🗄️ Database Schema Design

- **`customers`**: `customer_id` (PK), `customer_name`, `email`, `phone`, `city`, `state`, `signup_date`, `customer_segment`, `customer_tenure_days`. *(Indexes on `city`, `signup_date`, `customer_segment`)*
- **`transactions`**: `transaction_id` (PK), `customer_id` (FK), `transaction_date`, `product`, `category`, `quantity`, `unit_price`, `total_amount` (`DECIMAL(10,2)`), `payment_method`, `transaction_status`, `transaction_year`, `transaction_month`. *(Indexes on `customer_id`, `transaction_date`, `category`, `payment_method`, `transaction_status`)*

---

## 🚀 Quickstart

### 1. Setup Environment
```bash
python -m venv venv
source venv/bin/activate  # On Windows: .\venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

### 2. Configure Database
Copy `.env.example` to `.env` and set your local MySQL credentials:
```env
DB_HOST=localhost
DB_PORT=3306
DB_NAME=customer_analytics
DB_USER=root
DB_PASSWORD=your_mysql_password
```

### 3. Run Pipeline
```bash
python src/run_pipeline.py
```

---

## 📊 Sample Execution Summary

```text
================================================================================
                      PIPELINE EXECUTION SUMMARY
================================================================================
 Status                       : SUCCESS
 Execution Time               : 4.64 seconds
 Raw Records                  : 171 Customers | 680 Transactions
 Clean Records                : 147 Customers | 550 Transactions
 Invalid / Orphaned Isolated  : 100 Records (data/processed/invalid_transactions.csv)
 Calculated Total Revenue     : $980,026.00
 Validation Quality Gates     : PASSED (6/6 checks passed)
 MySQL Load Status            : SUCCESS
================================================================================
```

---

## 💻 Tech Stack

- **Language**: Python 3.11
- **Data Engineering**: Pandas, NumPy
- **Database**: MySQL 8.0, PyMySQL
- **Environment**: `python-dotenv`
- **Formats**: CSV, JSON, SQL
