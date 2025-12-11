{{
    config(
        materialized='view'
    )
}}

with source_data as (
    select * from {{ source('adventureworks', 'Customer') }}
),

transformed as (
    select
        customerid as id,
        accountnumber as "name",
        modifieddate as created_at,
        modifieddate as updated_at
    from source_data
)

select * from transformed
