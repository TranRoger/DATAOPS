{{
    config(
        materialized='table'
    )
}}

with bronze_customers as (
    select * from {{ ref('brnz_customers') }}
),

cleaned as (
    select
        customerid as customer_id,
        coalesce(firstname, 'Unknown') as first_name,
        coalesce(lastname, 'Unknown') as last_name,
        concat(
            coalesce(firstname, 'Unknown'),
            ' ',
            coalesce(lastname, 'Unknown')
        ) as full_name,
        emailpromotion as email_promotion,
        storeid as store_id,
        territoryid as territory_id,
        last_modified_date
    from bronze_customers
)

select * from cleaned
