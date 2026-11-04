#!/bin/bash
set -euo pipefail

psql -v ON_ERROR_STOP=1 \
     -v batch_pwd="$BATCH_PASSWORD" \
     -v herve_pwd="$HERVE_PASSWORD" \
     -v pascal_pwd="$PASCAL_PASSWORD" \
     -v airflow_pwd="$AIRFLOW_DB_PASSWORD" \
     --username "$POSTGRES_USER" --dbname "$POSTGRES_DB" <<'EOSQL'

-- ============================================================
-- Rôles, utilisateurs, base Airflow
-- ============================================================
CREATE ROLE airline_rw;

CREATE USER batch   WITH PASSWORD :'batch_pwd';
CREATE USER herve   WITH PASSWORD :'herve_pwd';
CREATE USER pascal  WITH PASSWORD :'pascal_pwd';
CREATE USER airflow WITH PASSWORD :'airflow_pwd';

CREATE DATABASE airflow OWNER airflow;

-- ============================================================
-- Schémas (créés avant les droits qui les référencent)
-- ============================================================
CREATE SCHEMA IF NOT EXISTS raw;
CREATE SCHEMA IF NOT EXISTS silver;
CREATE SCHEMA IF NOT EXISTS gold;

-- ============================================================
-- Droits
-- ============================================================
GRANT ALL PRIVILEGES ON DATABASE airline TO batch, herve, pascal;
GRANT ALL PRIVILEGES ON DATABASE airflow TO herve, pascal;

GRANT ALL PRIVILEGES ON SCHEMA raw TO batch;
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA raw TO batch, pascal;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA raw TO herve;

GRANT USAGE ON SCHEMA raw, silver, gold TO airline_rw;
GRANT ALL PRIVILEGES ON ALL TABLES    IN SCHEMA raw, silver, gold TO airline_rw;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA raw, silver, gold TO airline_rw;

-- Droits par défaut sur les futurs objets
ALTER DEFAULT PRIVILEGES IN SCHEMA raw, silver, gold
  GRANT ALL PRIVILEGES ON TABLES TO airline_rw;
ALTER DEFAULT PRIVILEGES FOR ROLE batch IN SCHEMA silver
  GRANT ALL PRIVILEGES ON TABLES TO airline_rw;
ALTER DEFAULT PRIVILEGES FOR ROLE batch IN SCHEMA silver
  GRANT ALL PRIVILEGES ON SEQUENCES TO airline_rw;

GRANT airline_rw TO airflow, herve, pascal, batch;
EOSQL