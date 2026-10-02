-- ============================================================================
-- SQL ANALYTICS QUERIES: Customer Data Processing & Analytics Pipeline
-- Database: customer_analytics
-- ============================================================================

USE customer_analytics;

-- ----------------------------------------------------------------------------
-- QUERY 1: Total Number of Customers
-- Purpose: Get total count of unique registered customers in the clean database.
-- ----------------------------------------------------------------------------
SELECT COUNT(customer_id) AS total_customers
FROM customers;


-- ----------------------------------------------------------------------------
-- QUERY 2: Total Number of Transactions
-- Purpose: Count total recorded transaction line-items.
-- ----------------------------------------------------------------------------
SELECT COUNT(transaction_id) AS total_transactions
FROM transactions;


-- ----------------------------------------------------------------------------
-- QUERY 3: Total Revenue
-- Purpose: Calculate total gross monetary revenue from successful/completed orders.
-- ----------------------------------------------------------------------------
SELECT SUM(total_amount) AS total_revenue
FROM transactions
WHERE transaction_status = 'Completed';


-- ----------------------------------------------------------------------------
-- QUERY 4: Average Transaction Value (AOV)
-- Purpose: Calculate average monetary order value across all completed transactions.
-- ----------------------------------------------------------------------------
SELECT ROUND(AVG(total_amount), 2) AS average_order_value
FROM transactions
WHERE transaction_status = 'Completed';


-- ----------------------------------------------------------------------------
-- QUERY 5: Revenue by City
-- Purpose: Aggregate total revenue generated across customer cities.
-- Demonstrates: INNER JOIN, GROUP BY, SUM, ORDER BY DESC.
-- ----------------------------------------------------------------------------
SELECT 
    c.city,
    COUNT(DISTINCT c.customer_id) AS customer_count,
    COUNT(t.transaction_id) AS total_orders,
    SUM(t.total_amount) AS city_revenue
FROM customers c
JOIN transactions t ON c.customer_id = t.customer_id
WHERE t.transaction_status = 'Completed'
GROUP BY c.city
ORDER BY city_revenue DESC;


-- ----------------------------------------------------------------------------
-- QUERY 6: Revenue by Product Category
-- Purpose: Summarize sales volume and revenue broken down by product category.
-- Demonstrates: GROUP BY, COUNT, SUM, AVG.
-- ----------------------------------------------------------------------------
SELECT 
    category,
    COUNT(transaction_id) AS order_count,
    SUM(quantity) AS total_units_sold,
    SUM(total_amount) AS category_revenue,
    ROUND(AVG(total_amount), 2) AS avg_category_order_value
FROM transactions
WHERE transaction_status = 'Completed'
GROUP BY category
ORDER BY category_revenue DESC;


-- ----------------------------------------------------------------------------
-- QUERY 7: Top 10 Customers by Total Spending
-- Purpose: Identify high-value customers (VIPs) for retention marketing.
-- Demonstrates: JOIN, SUM, GROUP BY, ORDER BY, LIMIT.
-- ----------------------------------------------------------------------------
SELECT 
    c.customer_id,
    c.customer_name,
    c.email,
    c.city,
    c.customer_segment,
    COUNT(t.transaction_id) AS completed_orders,
    SUM(t.total_amount) AS total_spent
FROM customers c
JOIN transactions t ON c.customer_id = t.customer_id
WHERE t.transaction_status = 'Completed'
GROUP BY c.customer_id, c.customer_name, c.email, c.city, c.customer_segment
ORDER BY total_spent DESC
LIMIT 10;


-- ----------------------------------------------------------------------------
-- QUERY 8: Monthly Revenue Breakdown
-- Purpose: Track monthly business revenue performance over time.
-- Demonstrates: DATE formatting / year-month grouping, SUM, ORDER BY.
-- ----------------------------------------------------------------------------
SELECT 
    transaction_year,
    transaction_month,
    COUNT(transaction_id) AS completed_transactions,
    SUM(total_amount) AS monthly_revenue
FROM transactions
WHERE transaction_status = 'Completed'
GROUP BY transaction_year, transaction_month
ORDER BY transaction_year ASC, transaction_month ASC;


-- ----------------------------------------------------------------------------
-- QUERY 9: Transaction Count & Revenue by Payment Method
-- Purpose: Determine payment preference trends among customers.
-- Demonstrates: GROUP BY, COUNT, SUM, Percentage calculation.
-- ----------------------------------------------------------------------------
SELECT 
    payment_method,
    COUNT(transaction_id) AS transaction_count,
    SUM(total_amount) AS total_revenue,
    ROUND(AVG(total_amount), 2) AS avg_transaction_value
FROM transactions
WHERE transaction_status = 'Completed'
GROUP BY payment_method
ORDER BY total_revenue DESC;


-- ----------------------------------------------------------------------------
-- QUERY 10: Successful vs Failed / Cancelled / Pending Transactions
-- Purpose: Evaluate transaction status distribution to measure order fulfillment rate.
-- Demonstrates: COUNT, CASE statements, SUM conditional aggregation.
-- ----------------------------------------------------------------------------
SELECT 
    transaction_status,
    COUNT(transaction_id) AS transaction_count,
    ROUND(COUNT(transaction_id) * 100.0 / (SELECT COUNT(*) FROM transactions), 2) AS percentage_of_total,
    SUM(total_amount) AS gross_amount
FROM transactions
GROUP BY transaction_status
ORDER BY transaction_count DESC;


-- ----------------------------------------------------------------------------
-- QUERY 11: Customers with No Transactions
-- Purpose: Find registered customers who have never placed a completed order (lead activation pool).
-- Demonstrates: LEFT JOIN with NULL condition filtering.
-- ----------------------------------------------------------------------------
SELECT 
    c.customer_id,
    c.customer_name,
    c.email,
    c.city,
    c.signup_date
FROM customers c
LEFT JOIN transactions t ON c.customer_id = t.customer_id AND t.transaction_status = 'Completed'
WHERE t.transaction_id IS NULL
ORDER BY c.signup_date DESC;


-- ----------------------------------------------------------------------------
-- QUERY 12: Top 10 Products by Revenue
-- Purpose: Identify top performing SKU catalog items.
-- Demonstrates: GROUP BY product, SUM, LIMIT.
-- ----------------------------------------------------------------------------
SELECT 
    product,
    category,
    SUM(quantity) AS units_sold,
    SUM(total_amount) AS total_product_revenue
FROM transactions
WHERE transaction_status = 'Completed'
GROUP BY product, category
ORDER BY total_product_revenue DESC
LIMIT 10;


-- ----------------------------------------------------------------------------
-- QUERY 13: Average Order Value (AOV) by Customer Segment
-- Purpose: Compare purchasing power across Consumer, Corporate, and Home Office segments.
-- Demonstrates: JOIN, GROUP BY segment, AVG, HAVING clause example.
-- ----------------------------------------------------------------------------
SELECT 
    c.customer_segment,
    COUNT(DISTINCT c.customer_id) AS active_customers,
    COUNT(t.transaction_id) AS completed_orders,
    SUM(t.total_amount) AS segment_revenue,
    ROUND(AVG(t.total_amount), 2) AS average_order_value
FROM customers c
JOIN transactions t ON c.customer_id = t.customer_id
WHERE t.transaction_status = 'Completed'
GROUP BY c.customer_segment
HAVING completed_orders > 5
ORDER BY average_order_value DESC;


-- ----------------------------------------------------------------------------
-- QUERY 14: Highest Revenue-Generating City
-- Purpose: Single query finding the #1 market location by sales revenue.
-- Demonstrates: JOIN, GROUP BY, ORDER BY DESC, LIMIT 1.
-- ----------------------------------------------------------------------------
SELECT 
    c.city,
    c.state,
    SUM(t.total_amount) AS total_revenue
FROM customers c
JOIN transactions t ON c.customer_id = t.customer_id
WHERE t.transaction_status = 'Completed'
GROUP BY c.city, c.state
ORDER BY total_revenue DESC
LIMIT 1;


-- ----------------------------------------------------------------------------
-- QUERY 15: Monthly Transaction Volume and Revenue Trend
-- Purpose: Provide executive summary metrics grouped by year and month.
-- Demonstrates: COUNT, SUM, AVG aggregate metrics in single time-series view.
-- ----------------------------------------------------------------------------
SELECT 
    transaction_year,
    transaction_month,
    COUNT(transaction_id) AS total_orders,
    SUM(quantity) AS total_items_sold,
    SUM(total_amount) AS total_revenue,
    ROUND(AVG(total_amount), 2) AS avg_order_value
FROM transactions
WHERE transaction_status = 'Completed'
GROUP BY transaction_year, transaction_month
ORDER BY transaction_year DESC, transaction_month DESC;
