with product as (
    select * from {{ source('adventureworks_production', 'Product') }}
),

product_subcategory as (
    select *
    from {{ source('adventureworks_production', 'ProductSubcategory') }}
),

staged as (
    select
        p.productid,
        p.name as productname,
        p.productnumber,
        p.makeflag,
        p.finishedgoodsflag,
        p.color,
        p.safetystocklevel,
        p.reorderpoint,
        p.standardcost,
        p.listprice,
        p.size,
        p.sizeunitmeasurecode,
        p.weightunitmeasurecode,
        p.weight,
        p.daystomanufacture,
        p.productline,
        p.class,
        p.style,
        p.productsubcategoryid,
        p.productmodelid,
        p.sellstartdate,
        p.sellenddate,
        p.discontinueddate,
        ps.name as subcategoryname,
        ps.productcategoryid,
        p.modifieddate as last_modified_date
    from product as p
    left join product_subcategory as ps
        on p.productsubcategoryid = ps.productsubcategoryid
)

select * from staged
