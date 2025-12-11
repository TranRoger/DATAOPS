{{
    config(
        materialized='view'
    )
}}

with source as (
    select * from {{ source('adventureworks', 'Customer') }}
),

person as (
    select * from {{ source('adventureworks_person', 'Person') }}
),

staged as (
    select
        c.customerid,
        p.firstname,
        p.lastname,
        p.emailpromotion,
        c.storeid,
        c.territoryid,
        c.modifieddate as last_modified_date
    from source as c
    left join person as p
        on c.personid = p.businessentityid
)

select * from staged
