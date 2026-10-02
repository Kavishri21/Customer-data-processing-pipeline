-- ============================================================================
-- DATABASE SCHEMA: Customer Data Processing & Analytics Pipeline
-- Database: customer_analytics
-- Target DBMS: MySQL 8.0+
-- ============================================================================

-- Create Database if not exists
CREATE DATABASE IF NOT EXISTS customer_analytics;
USE customer_analytics;

-- Drop existing tables to ensure clean state during deployment
DROP TABLE IF EXISTS transactions;
DROP TABLE IF EXISTS customers;

-- ----------------------------------------------------------------------------
-- TABLE 1: customers
-- Purpose: Holds cleaned profile information for registered customers.
--
-- Data Type Rationale:
-- - customer_id (VARCHAR(20)): Primary key matching string IDs like 'CUST-1001'.
-- - customer_name (VARCHAR(100)): Accommodates long Indian/international names.
-- - email (VARCHAR(100)): Standard length for email addresses; NULL allowed.
-- - phone (VARCHAR(20)): String representation to preserve leading zeros or country codes.
-- - city / state (VARCHAR(50)): Standardized geographical location names.
-- - signup_date (DATE): Year-Month-Day format for demographic filtering.
-- - customer_segment (VARCHAR(30)): Customer classification ('Consumer', 'Corporate', etc.).
-- - customer_tenure_days (INT): Metric representing days active since signup.
-- ----------------------------------------------------------------------------
CREATE TABLE customers (
    customer_id VARCHAR(20) PRIMARY KEY,
    customer_name VARCHAR(100) NOT NULL,
    email VARCHAR(100) NULL,
    phone VARCHAR(20) DEFAULT 'Unknown',
    city VARCHAR(50) DEFAULT 'Unknown',
    state VARCHAR(50) DEFAULT 'Unknown',
    signup_date DATE NOT NULL,
    customer_segment VARCHAR(30) DEFAULT 'Consumer',
    customer_tenure_days INT DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- Indexes on customers table for fast filtered queries
CREATE INDEX idx_customers_city ON customers(city);
CREATE INDEX idx_customers_signup_date ON customers(signup_date);
CREATE INDEX idx_customers_segment ON customers(customer_segment);


-- ----------------------------------------------------------------------------
-- TABLE 2: transactions
-- Purpose: Holds cleaned transaction line-item records linked to customers.
--
-- Data Type Rationale:
-- - transaction_id (VARCHAR(30)): Primary key matching IDs like 'TXN-10001'.
-- - customer_id (VARCHAR(20)): Foreign key linking to customers table.
-- - transaction_date (DATETIME): Full precision timestamp of purchase.
-- - quantity (INT): Discrete item count (enforced > 0).
-- - unit_price (DECIMAL(10,2)): Fixed-point decimal to prevent IEEE 754 float rounding errors in financial transactions.
-- - total_amount (DECIMAL(10,2)): Pre-calculated order line total (quantity * unit_price).
-- - payment_method (VARCHAR(30)): Standardized payment method identifier.
-- - transaction_status (VARCHAR(20)): Processing state ('Completed', 'Pending', 'Failed', 'Cancelled').
-- - transaction_year / month (INT): Extracted temporal partitioning keys.
-- ----------------------------------------------------------------------------
CREATE TABLE transactions (
    transaction_id VARCHAR(30) PRIMARY KEY,
    customer_id VARCHAR(20) NOT NULL,
    transaction_date DATETIME NOT NULL,
    product VARCHAR(100) NOT NULL,
    category VARCHAR(50) NOT NULL,
    quantity INT NOT NULL CHECK (quantity > 0),
    unit_price DECIMAL(10, 2) NOT NULL CHECK (unit_price > 0),
    total_amount DECIMAL(10, 2) NOT NULL CHECK (total_amount > 0),
    payment_method VARCHAR(30) NOT NULL,
    transaction_status VARCHAR(20) NOT NULL,
    transaction_year INT NOT NULL,
    transaction_month INT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    -- Foreign Key Constraint ensuring referential integrity
    CONSTRAINT fk_txns_customer
        FOREIGN KEY (customer_id) 
        REFERENCES customers(customer_id)
        ON DELETE CASCADE
        ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- Indexes on transactions table for JOIN and aggregation performance
CREATE INDEX idx_txns_cust_id ON transactions(customer_id);
CREATE INDEX idx_txns_date ON transactions(transaction_date);
CREATE INDEX idx_txns_category ON transactions(category);
CREATE INDEX idx_txns_payment_method ON transactions(payment_method);
CREATE INDEX idx_txns_status ON transactions(transaction_status);
