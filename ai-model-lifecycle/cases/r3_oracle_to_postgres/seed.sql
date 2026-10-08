-- R3 seed fixture — small deterministic dataset used to exercise both procs
-- and to produce the golden result sets. Loaded by the scorer BEFORE running the
-- model's translation, so parity is apples-to-apples.

TRUNCATE customers, orders, products, order_items RESTART IDENTITY CASCADE;

INSERT INTO customers (customer_id, customer_name, status) VALUES
    (1, 'Acme Corp',      'ACTIVE'),
    (2, 'Globex',         'ACTIVE'),
    (3, 'Initech',        'INACTIVE'),
    (4, 'Umbrella',       'ACTIVE'),
    (5, 'Stark Industries','ACTIVE');

INSERT INTO orders (order_id, customer_id, order_total, order_date) VALUES
    (101, 1, 750.00, now()),
    (102, 1, 400.00, now()),   -- Acme total 1150 -> GOLD
    (103, 2, 300.00, now()),
    (104, 2, 250.00, now()),   -- Globex total 550 -> SILVER
    (105, 3, 900.00, now()),   -- INACTIVE -> excluded
    (106, 4, 120.00, now()),   -- Umbrella total 120 -> BRONZE
    (107, 5, 2000.00, now());  -- Stark total 2000 -> GOLD

INSERT INTO products (product_id, product_name, category) VALUES
    (1, 'Widget',   'HARDWARE'),
    (2, 'Gadget',   'HARDWARE'),
    (3, 'License',  'SOFTWARE'),
    (4, 'Support',  'SERVICES');

INSERT INTO order_items (order_item_id, order_id, product_id, quantity, unit_price) VALUES
    (1, 101, 1, 10, 50.00),    -- HARDWARE 500
    (2, 101, 3,  2, 100.00),   -- SOFTWARE 200
    (3, 102, 2,  5, 20.00),    -- HARDWARE 100
    (4, 103, 4,  1, 300.00),   -- SERVICES 300
    (5, 106, 3,  1, 120.00);   -- SOFTWARE 120
