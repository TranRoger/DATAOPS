-- Test: All orders must have valid customers
SELECT
    o.sales_order_id,
    o.customer_id
FROM {{ ref('brnz_sales_orders') }} o
LEFT JOIN {{ ref('brnz_customers') }} c
    ON o.customer_id = c.CustomerID
WHERE c.CustomerID IS NULL
