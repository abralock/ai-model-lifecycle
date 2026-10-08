-- 01_init.sql — placeholder bootstrap for the Gate 1 dev box database.
--
-- This file is executed by the postgres:16 image on FIRST container start
-- (only when the pgdata volume is empty). Keep it idempotent.
--
-- NOTE: real test schema is owned by Pikachu's artifacts (cases/ + golden_set).
-- Only add sandbox/smoke objects here, nothing that evaluates a model.

-- Smoke-test table so R4/R5 harness runs have something to prove connectivity.
CREATE TABLE IF NOT EXISTS smoke_health (
    id          serial PRIMARY KEY,
    checked_at  timestamptz NOT NULL DEFAULT now(),
    note        text
);

INSERT INTO smoke_health (note) VALUES ('init placeholder');
