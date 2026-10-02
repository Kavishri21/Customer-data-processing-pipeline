"""
MySQL Database Load Pipeline for Customer Data Processing & Analytics Pipeline

Handles:
- Loading environment variables from .env file
- Establishing secure database connection to MySQL
- Initializing database schema from sql/schema.sql
- Performing bulk/batch insertion of cleaned customers and transactions
- Executing SQL verification query
"""

import os
import sys
import warnings
import pandas as pd
from dotenv import load_dotenv

warnings.filterwarnings('ignore', category=UserWarning)

try:
    import pymysql
except ImportError:
    print("Error: 'pymysql' package is required. Install via: pip install pymysql")
    sys.exit(1)


def get_db_connection(include_db=True):
    """
    Reads credentials from .env and establishes PyMySQL connection.
    """
    load_dotenv()
    
    host = os.getenv("DB_HOST", "localhost")
    port = int(os.getenv("DB_PORT", 3306))
    user = os.getenv("DB_USER", "root")
    password = os.getenv("DB_PASSWORD", "")
    db_name = os.getenv("DB_NAME", "customer_analytics")

    try:
        if include_db:
            conn = pymysql.connect(
                host=host,
                port=port,
                user=user,
                password=password,
                database=db_name,
                autocommit=True,
                cursorclass=pymysql.cursors.DictCursor
            )
        else:
            conn = pymysql.connect(
                host=host,
                port=port,
                user=user,
                password=password,
                autocommit=True,
                cursorclass=pymysql.cursors.DictCursor
            )
        return conn
    except pymysql.MySQLError as e:
        raise ConnectionError(
            f"Failed to connect to MySQL database at {host}:{port} as user '{user}'.\n"
            f"Error details: {e}\n"
            f"Please check your .env configuration file and verify MySQL server is running."
        )


def parse_sql_statements(sql_text):
    """Cleanly strips SQL comments and splits into executable statements."""
    lines = []
    for line in sql_text.splitlines():
        line_clean = line.strip()
        if not line_clean or line_clean.startswith('--') or line_clean.startswith('#'):
            continue
        lines.append(line)
    
    clean_sql = "\n".join(lines)
    statements = [stmt.strip() for stmt in clean_sql.split(";") if stmt.strip()]
    return statements


def initialize_schema(schema_file="sql/schema.sql"):
    """Reads schema.sql and creates database & tables."""
    print("Initializing MySQL Database Schema...")
    
    # 1. Connect without DB selected to ensure database exists
    conn = get_db_connection(include_db=False)
    with conn.cursor() as cursor:
        cursor.execute("CREATE DATABASE IF NOT EXISTS customer_analytics;")
    conn.close()

    # 2. Connect with DB selected and run DDL commands
    conn = get_db_connection(include_db=True)
    with open(schema_file, "r", encoding="utf-8") as f:
        schema_sql = f.read()

    statements = parse_sql_statements(schema_sql)
    
    with conn.cursor() as cursor:
        for stmt in statements:
            if stmt.upper().startswith("USE "):
                continue
            cursor.execute(stmt)
    
    conn.close()
    print("Database schema initialized successfully.")


def load_data_to_mysql(cust_path="data/processed/customers_clean.csv",
                       txn_path="data/processed/transactions_clean.csv"):
    """Reads processed CSVs and inserts data into MySQL tables."""
    print("Loading clean datasets into MySQL...")
    
    if not os.path.exists(cust_path) or not os.path.exists(txn_path):
        raise FileNotFoundError("Processed CSV files not found for database load.")

    df_cust = pd.read_csv(cust_path)
    df_txn = pd.read_csv(txn_path)

    conn = get_db_connection(include_db=True)
    with conn.cursor() as cursor:
        cursor.execute("SET FOREIGN_KEY_CHECKS = 0;")
        cursor.execute("TRUNCATE TABLE transactions;")
        cursor.execute("TRUNCATE TABLE customers;")
        cursor.execute("SET FOREIGN_KEY_CHECKS = 1;")

        # Insert Customers
        cust_sql = """
            INSERT INTO customers (
                customer_id, customer_name, email, phone, city, state, 
                signup_date, customer_segment, customer_tenure_days
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
        """
        cust_tuples = [
            (
                row['customer_id'],
                row['customer_name'],
                None if pd.isnull(row['email']) else row['email'],
                row['phone'],
                row['city'],
                row['state'],
                row['signup_date'],
                row['customer_segment'],
                int(row['customer_tenure_days'])
            )
            for _, row in df_cust.iterrows()
        ]
        cursor.executemany(cust_sql, cust_tuples)
        print(f"Inserted {len(cust_tuples)} records into 'customers' table.")

        # Insert Transactions
        txn_sql = """
            INSERT INTO transactions (
                transaction_id, customer_id, transaction_date, product, category,
                quantity, unit_price, total_amount, payment_method, transaction_status,
                transaction_year, transaction_month
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """
        txn_tuples = [
            (
                row['transaction_id'],
                row['customer_id'],
                row['transaction_date'],
                row['product'],
                row['category'],
                int(row['quantity']),
                float(row['unit_price']),
                float(row['total_amount']),
                row['payment_method'],
                row['transaction_status'],
                int(row['transaction_year']),
                int(row['transaction_month'])
            )
            for _, row in df_txn.iterrows()
        ]
        cursor.executemany(txn_sql, txn_tuples)
        print(f"Inserted {len(txn_tuples)} records into 'transactions' table.")

    conn.close()
    print("Data loading completed successfully!")


def export_analytics_results():
    """Executes sample analytics queries and exports results to CSV files."""
    analytics_dir = "reports/analytics_results"
    os.makedirs(analytics_dir, exist_ok=True)
    
    try:
        conn = get_db_connection(include_db=True)
        
        sql_city = """
            SELECT c.city, COUNT(t.transaction_id) AS total_orders, SUM(t.total_amount) AS revenue
            FROM customers c JOIN transactions t ON c.customer_id = t.customer_id
            WHERE t.transaction_status = 'Completed'
            GROUP BY c.city ORDER BY revenue DESC;
        """
        df_city = pd.read_sql(sql_city, conn)
        df_city.to_csv(os.path.join(analytics_dir, "revenue_by_city.csv"), index=False)

        sql_cat = """
            SELECT category, COUNT(transaction_id) AS order_count, SUM(total_amount) AS revenue
            FROM transactions WHERE transaction_status = 'Completed'
            GROUP BY category ORDER BY revenue DESC;
        """
        df_cat = pd.read_sql(sql_cat, conn)
        df_cat.to_csv(os.path.join(analytics_dir, "revenue_by_category.csv"), index=False)

        sql_top_cust = """
            SELECT c.customer_id, c.customer_name, c.city, SUM(t.total_amount) AS total_spent
            FROM customers c JOIN transactions t ON c.customer_id = t.customer_id
            WHERE t.transaction_status = 'Completed'
            GROUP BY c.customer_id, c.customer_name, c.city ORDER BY total_spent DESC LIMIT 10;
        """
        df_top_cust = pd.read_sql(sql_top_cust, conn)
        df_top_cust.to_csv(os.path.join(analytics_dir, "top_customers.csv"), index=False)

        conn.close()
        print(f"Exported sample analytics reports to {analytics_dir}/")
    except Exception as e:
        print(f"[NOTE] Skipping analytics export: {e}")


def run_load_pipeline():
    """Wrapper function to initialize schema and load data."""
    try:
        initialize_schema()
        load_data_to_mysql()
        export_analytics_results()
        return True
    except ConnectionError as ce:
        print(f"\n[MYSQL CONNECTION ERROR] {ce}")
        print("Pipeline continued without MySQL database load. Processed CSV files remain available in data/processed/")
        return False
    except Exception as ex:
        print(f"\n[MYSQL LOAD ERROR] {ex}")
        return False


if __name__ == "__main__":
    run_load_pipeline()
