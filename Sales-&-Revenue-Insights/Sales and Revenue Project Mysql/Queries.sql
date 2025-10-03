-- Total revenue earned across all orders
select sum(total_amount) as total_revenue
from orders;

-- sales revenue per month for the year 2025.
select date_format(order_date,'%M') as month,
sum(total_amount) as monthly_sales
from orders
group by month
order by month;

-- Top 5 customers spent the most money overall
select customers.customer_name,sum(orders.total_amount) as money_spent
from customers
left join orders on customers.customer_id=orders.customer_id
group by customers.customer_name
order by money_spent desc
limit 5;