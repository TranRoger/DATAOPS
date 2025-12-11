{{
    config(
        materialized='table'
    )
}}

with bronze_products as (
    select * from {{ ref('brnz_products') }}
),

cleaned as (
    select
        *,
        productid as product_id,
        productname as product_name,
        productnumber as product_number,
        coalesce(color, 'N/A') as color,
        standardcost as standard_cost,
        listprice as list_price,
        coalesce(size, 'N/A') as size,
        coalesce(weight, 0) as weight,
        productline as product_line,
        class as "class",
        style as style,
        productsubcategoryid as subcategory_id,
        coalesce(
            subcategoryname,
            'Uncategorized'
        ) as subcategory_name,
        productcategoryid as category_id,
        sellstartdate as sell_start_date,
        sellenddate as sell_end_date,
        case
            when discontinueddate is not null then 1
            else 0
        end as is_discontinued,
        last_modified_date
    from bronze_products
)

select * from cleaned
