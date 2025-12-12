with sales_order_header as (
    select
        salesorderid as sales_order_id,
        orderdate as order_date,
        duedate as due_date,
        shipdate as ship_date,
        totaldue as total_due,
        [status] as order_status,
        onlineorderflag as online_order_flag,
        salesordernumber as sales_order_number,
        purchaseordernumber as purchase_order_number,
        customerid as customer_id,
        salespersonid as sales_person_id,
        territoryid as territory_id
    from {{ source('adventureworks', 'SalesOrderHeader') }}
),

sales_order_detail as (
    select
        salesorderdetailid as order_detail_id,
        salesorderid as sales_order_id,
        productid as product_id,
        orderqty as order_qty,
        unitprice as unit_price,
        unitpricediscount as unit_price_discount,
        linetotal as line_total
    from {{ source('adventureworks', 'SalesOrderDetail') }}
)

select
    h.sales_order_id,
    h.order_date,
    h.due_date,
    h.ship_date,
    h.total_due,
    h.order_status,
    h.online_order_flag,
    h.sales_order_number,
    h.purchase_order_number,
    h.customer_id,
    h.sales_person_id,
    h.territory_id,
    d.order_detail_id,
    d.product_id,
    d.order_qty,
    d.unit_price,
    d.unit_price_discount,
    d.line_total
from sales_order_header as h
left join sales_order_detail as d
    on h.sales_order_id = d.sales_order_id
