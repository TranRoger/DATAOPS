{{
    config(
        materialized='table'
    )
}}

with products as (
    select * from {{ ref('slvr_products') }}
),

sales as (
    select * from {{ ref('slvr_sales_orders') }}
),

product_sales as (
    select
        p.product_id,
        p.product_name,
        p.subcategory_name,
        p.color,
        p.list_price,
        p.standard_cost,
        count(distinct s.sales_order_id) as total_orders,
        coalesce(sum(s.order_qty), 0) as total_quantity_sold,
        coalesce(sum(s.line_total), 0) as total_revenue,
        avg(s.unit_price) as avg_selling_price,
        coalesce(sum(s.line_total), 0)
            - (coalesce(sum(s.order_qty), 0) * p.standard_cost)
            as total_profit,
        case
            when sum(s.order_qty) > 0
                then
                    (
                        sum(s.line_total)
                            - (sum(s.order_qty) * p.standard_cost)
                    ) / sum(s.line_total) * 100
            else 0
        end as profit_margin_pct
    from products as p
    left join sales as s
        on p.product_id = s.product_id
    group by
        p.product_id,
        p.product_name,
        p.subcategory_name,
        p.color,
        p.list_price,
        p.standard_cost
)

select * from product_sales
