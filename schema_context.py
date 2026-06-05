"""Olist ERD 기준 테이블 관계·컬럼 위치 힌트 (Text-to-SQL용)."""

# create_sql_query_chain 프롬프트에 항상 주입
SCHEMA_RELATIONSHIPS = """
## 테이블 관계 (JOIN 시 반드시 참고)
- orders.customer_id = customers.customer_id  → 고객 도시/주: customers.customer_city, customers.customer_state
- orders.order_id = order_items.order_id      → 매출·주문 금액: order_items.price, order_items.freight_value
- order_items.product_id = products.product_id → 상품 카테고리: products.product_category_name
- order_items.seller_id = sellers.seller_id   → 판매자 도시: sellers.seller_city (고객 도시와 다름)
- orders.order_id = order_payments.order_id
- orders.order_id = order_reviews.order_id
- customers.customer_zip_code_prefix = geolocation.geolocation_zip_code_prefix (지역 좌표·도시 참고 시)
- sellers.seller_zip_code_prefix = geolocation.geolocation_zip_code_prefix

## 자주 하는 실수 (금지)
- orders 테이블에는 customer_city, customer_state 컬럼이 없음 → customers 조인 필수
- 매출/매출액 질문은 보통 order_items.price 합산 + orders·order_items 조인
- "도시별 매출"이 고객 기준이면 customers.customer_city, 판매자 기준이면 sellers.seller_city

## 예시 (고객 도시별 매출 상위)
SELECT c.customer_city, SUM(oi.price) AS total_revenue
FROM orders o
JOIN order_items oi ON o.order_id = oi.order_id
JOIN customers c ON o.customer_id = c.customer_id
GROUP BY c.customer_city
ORDER BY total_revenue DESC
LIMIT 5;

1. Order count / 주문 수 / 주문건수
- Count orders from orders table.
- Exclude canceled and unavailable orders.
- Required filter:
  orders.order_status NOT IN ('canceled', 'unavailable')

2. Monthly / 월별
- Use year-month format.
- MySQL expression:
  DATE_FORMAT(orders.order_purchase_timestamp, '%Y-%m')
- Do not use MONTH(order_purchase_timestamp) alone because it mixes years.

3. Revenue / sales / 매출
- Use order_items.price.
- Join orders and order_items.
- Exclude canceled and unavailable orders.

4. Customer region / city / state
- customer_city and customer_state are in customers table.
- Join customers on orders.customer_id = customers.customer_id.
"""

# SQLDatabase.custom_table_info — 테이블별로 LLM에 보강 설명
CUSTOM_TABLE_INFO = {
    "orders": (
        "Central order table. PK: order_id. FK: customer_id -> customers.customer_id. "
        "Columns: order_status, order_purchase_timestamp, order_approved_at, "
        "order_delivered_carrier_date, order_delivered_customer_date, order_estimated_delivery_date. "
        "NO customer_city here — join customers for customer location."
    ),
    "customers": (
        "Customer master. PK: customer_id. "
        "Location columns: customer_city, customer_state, customer_zip_code_prefix. "
        "Join orders ON orders.customer_id = customers.customer_id."
    ),
    "order_items": (
        "Line items per order. FK: order_id -> orders, product_id -> products, seller_id -> sellers. "
        "Revenue fields: price, freight_value. shipping_limit_date."
    ),
    "products": (
        "Product catalog. PK: product_id. "
        "Category: product_category_name. Also dimensions/weight columns."
    ),
    "sellers": (
        "Seller master. PK: seller_id. "
        "Location: seller_city, seller_state, seller_zip_code_prefix (not customer_city)."
    ),
    "order_payments": (
        "Payments per order. FK: order_id -> orders. "
        "Columns: payment_sequential, payment_type, payment_installments, payment_value."
    ),
    "order_reviews": (
        "Reviews per order. FK: order_id -> orders. "
        "Columns: review_id, review_score, review_comment_title, review_comment_message, dates."
    ),
    "geolocation": (
        "Zip prefix to lat/lng/city/state. "
        "Join via customer_zip_code_prefix or seller_zip_code_prefix = geolocation_zip_code_prefix."
    ),
}
