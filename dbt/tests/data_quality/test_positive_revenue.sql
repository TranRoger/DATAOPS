-- Test: All revenue values must be positive
SELECT
    sales_order_id,
    line_total
FROM {{ ref('brnz_sales_orders') }}
WHERE line_total < 0
