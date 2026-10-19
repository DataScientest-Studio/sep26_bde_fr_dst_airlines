FROM ghcr.io/dbt-labs/dbt-postgres:1.10.0

WORKDIR /app

COPY . /app

COPY docker/dbt/entrypoint.sh /entrypoint.sh

RUN chmod +x /entrypoint.sh

ENTRYPOINT ["/entrypoint.sh"]