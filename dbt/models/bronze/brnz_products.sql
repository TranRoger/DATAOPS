with staged as (
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
        p.class as productclass,
        p.style,
        p.productsubcategoryid,
        p.productmodelid,
        p.sellstartdate,
        p.sellenddate,
        p.discontinueddate,
        ps.name as subcategoryname,
        ps.productcategoryid,
        p.modifieddate as last_modified_date
    from {{ source('adventureworks_production', 'Product') }} as p
    left join {{ source('adventureworks_production', 'ProductSubcategory') }} as ps
        on p.productsubcategoryid = ps.productsubcategoryid
)

select * from staged
