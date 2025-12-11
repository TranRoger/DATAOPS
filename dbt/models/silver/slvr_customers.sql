{{
    config(
        materialized='table'
    )
}}

with cleaned as (
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
    from {{ ref('brnz_customers') }}
)

select * from cleaned
