-- CUSTOMERS
ALTER TABLE customers
    ADD PRIMARY KEY (customer_id);

-- SELLERS
ALTER TABLE sellers
    ADD PRIMARY KEY (seller_id);

-- PRODUCTS
ALTER TABLE products
    ADD PRIMARY KEY (product_id);

-- ORDERS
ALTER TABLE orders
    ADD PRIMARY KEY (order_id),
    ADD FOREIGN KEY (customer_id) REFERENCES customers(customer_id);

-- ORDER ITEMS
ALTER TABLE order_items
    ADD PRIMARY KEY (order_id, order_item_id),
    ADD FOREIGN KEY (order_id)   REFERENCES orders(order_id),
    ADD FOREIGN KEY (product_id) REFERENCES products(product_id),
    ADD FOREIGN KEY (seller_id)  REFERENCES sellers(seller_id);

-- ORDER PAYMENTS
ALTER TABLE order_payments
    ADD FOREIGN KEY (order_id) REFERENCES orders(order_id);

-- ORDER REVIEWS (no PK — review_id has duplicates in raw Olist data)
ALTER TABLE order_reviews
    ADD FOREIGN KEY (order_id) REFERENCES orders(order_id);

-- PRODUCT CATEGORY TRANSLATION
ALTER TABLE product_category_translation
    ADD PRIMARY KEY (product_category_name);

-- USEFUL INDEXES FOR QUERY PERFORMANCE
CREATE INDEX IF NOT EXISTS idx_orders_status       ON orders(order_status);
CREATE INDEX IF NOT EXISTS idx_orders_purchase_ts  ON orders(order_purchase_timestamp);
CREATE INDEX IF NOT EXISTS idx_order_items_product ON order_items(product_id);
CREATE INDEX IF NOT EXISTS idx_order_items_seller  ON order_items(seller_id);
CREATE INDEX IF NOT EXISTS idx_reviews_score       ON order_reviews(review_score);
CREATE INDEX IF NOT EXISTS idx_reviews_id ON order_reviews(review_id);
