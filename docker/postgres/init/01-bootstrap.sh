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


EOSQL

