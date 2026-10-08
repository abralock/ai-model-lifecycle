#!/usr/bin/env python3
"""R4 seed — generate a deterministic bulk dataset for the optimize task.

Creates N rows across customers/products/orders/order_items (default 100,000
orders) using a fixed RNG seed so the data — and therefore the EXPLAIN plan and
latency threshold — is reproducible.

Usage:
    python seed.py --dsn "host=localhost port=5432 dbname=aidb user=ai password=ai"
    python seed.py --rows 100000          # default
    python seed.py --print-only           # emit SQL to stdout, no DB needed

The scorer imports `build_sql(rows, seed)` so seeding stays in one place.
"""

from __future__ import annotations

import argparse
import random
from datetime import date, timedelta


def build_sql(rows: int = 100_000, seed: int = 42) -> str:
    """Return a self-contained SQL script inserting a deterministic dataset.

    Uses generate_series for speed (100k rows in <1s) instead of a Python loop.
    Distribution is crafted so the target query's filter is selective enough
    (~15% COMPLETED within date range) that an index scan is clearly better.
    """
    rng = random.Random(seed)
    customers = 5_000
    products = 200
    # date window: 2025-06-01 .. 2026-09-30
    start = date(2025, 6, 1)
    days = 486

    return f"""
TRUNCATE order_items, orders, products, customers RESTART IDENTITY CASCADE;

INSERT INTO customers (customer_id, customer_name, email, country)
SELECT g,
       'Customer ' || g,
       'customer' || g || '@example.com',
       (ARRAY['US','GB','DE','FR','JP','BR','IN','CA'])[1 + (g % 8)]
FROM   generate_series(1, {customers}) AS g;

INSERT INTO products (product_id, product_name, category, unit_price)
SELECT g,
       'Product ' || g,
       (ARRAY['HARDWARE','SOFTWARE','SERVICES','ACCESSORIES','SUBSCRIPTION'])[1 + (g % 5)],
       round((10 + (g % 90) * 1.37)::numeric, 2)
FROM   generate_series(1, {products}) AS g;

INSERT INTO orders (order_id, customer_id, order_date, status, total_amount)
SELECT g,
       1 + (g % {customers}),
       DATE '2025-06-01' + ((g * 7919) % {days}) * INTERVAL '1 day',
       (ARRAY['COMPLETED','COMPLETED','COMPLETED','PENDING','CANCELLED','REFUNDED'])[1 + (g % 6)],
       round((50 + (g % 5000) * 0.73)::numeric, 2)
FROM   generate_series(1, {rows}) AS g;

INSERT INTO order_items (order_item_id, order_id, product_id, quantity, unit_price)
SELECT g,
       1 + (g % {rows}),
       1 + (g % {products}),
       1 + (g % 5),
       round((10 + (g % 90) * 1.37)::numeric, 2)
FROM   generate_series(1, {rows}) AS g;

ANALYZE customers; ANALYZE products; ANALYZE orders; ANALYZE order_items;
""".strip()


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="R4 bulk-data seeder")
    ap.add_argument("--rows", type=int, default=100_000)
    ap.add_argument("--seed", type=int, default=42)
    ap.add_argument("--dsn", default=None, help="psycopg2 DSN; omit to print SQL")
    ap.add_argument("--print-only", action="store_true")
    args = ap.parse_args(argv)

    sql = build_sql(args.rows, args.seed)

    if args.print_only or not args.dsn:
        print(sql)
        return 0

    try:
        import psycopg2  # type: ignore
    except Exception as exc:  # pragma: no cover
        print(f"psycopg2 unavailable ({exc}); run with --print-only", flush=True)
        return 2

    with psycopg2.connect(args.dsn) as conn:
        with conn.cursor() as cur:
            cur.execute(sql)
        conn.commit()
    print(f"seeded {args.rows} orders (+items) into {args.dsn.split('dbname=')[-1]}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
