#!/bin/sh

mkdir -p ~/.dbt

cat > ~/.dbt/profiles.yml << EOF
airline:
  target: dev

  outputs:
    dev:
      type: postgres
      host: ${DBT_HOST}
      user: ${DBT_USER}
      password: ${DBT_PASSWORD}
      port: ${DBT_PORT}
      dbname: ${DBT_DATABASE}
      schema: ${DBT_SCHEMA}
      threads: 1
EOF

echo "DBT profile generated"

exec "$@"