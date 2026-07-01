-- Target table DDL for current-state orders.

CREATE TABLE IF NOT EXISTS orders_current_state (
    id              INT PRIMARY KEY,
    customer_name   VARCHAR(100),
    order_total     NUMERIC(10,2),
    status          VARCHAR(20),
    updated_at      TIMESTAMP NOT NULL,
    synced_at       TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_orders_updated_at ON orders_current_state(updated_at);
CREATE INDEX IF NOT EXISTS idx_orders_status ON orders_current_state(status);

-- Production upsert pattern:
-- INSERT INTO orders_current_state (id, customer_name, order_total, status, updated_at)
-- VALUES (%s, %s, %s, %s, %s)
-- ON CONFLICT (id) DO UPDATE SET
--   customer_name = EXCLUDED.customer_name,
--   order_total   = EXCLUDED.order_total,
--   status        = EXCLUDED.status,
--   updated_at    = EXCLUDED.updated_at,
--   synced_at     = CURRENT_TIMESTAMP
-- WHERE EXCLUDED.updated_at > orders_current_state.updated_at;
