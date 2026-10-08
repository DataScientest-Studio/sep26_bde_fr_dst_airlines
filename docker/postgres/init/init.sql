-- ============================================================
-- Airline
-- ============================================================
CREATE USER batch WITH PASSWORD 'M0woDa24FDEw4Kf3fDC62vyYo1fwb47x';
GRANT ALL PRIVILEGES ON DATABASE airline TO batch;
GRANT ALL PRIVILEGES ON SCHEMA raw TO batch;
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA raw TO batch;
CREATE USER herve WITH PASSWORD 'nslfkUUdQ6xXZsM74G48K7xB6xAnlAd9';
GRANT ALL PRIVILEGES ON DATABASE airline TO herve;
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA raw TO herve;
CREATE USER pascal WITH PASSWORD 'RyuaOrhaERktczXaLj32hPak4a0U8OmQ';
GRANT ALL PRIVILEGES ON DATABASE airline TO pascal;
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA raw TO pascal;


-- ============================================================
-- Airflow
-- ============================================================

CREATE USER airflow WITH PASSWORD 'HJqCh5uMtV19qUOXg47K6r08SsFwHHtk';
CREATE DATABASE airflow OWNER airflow;
GRANT ALL PRIVILEGES ON DATABASE airflow TO herve;
GRANT ALL PRIVILEGES ON DATABASE airflow TO pascal;