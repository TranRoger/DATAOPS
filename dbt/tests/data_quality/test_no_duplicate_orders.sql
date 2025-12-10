-- Test: No duplicate order detail IDs should exist
SELECT
    order_detail_id,
    COUNT(*) as duplicate_count
FROM {{ ref('brnz_sales_orders') }}
GROUP BY order_detail_id
HAVING COUNT(*) > 1
