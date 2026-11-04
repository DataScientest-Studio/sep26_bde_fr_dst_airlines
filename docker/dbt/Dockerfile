###########################################################
# DBT Dockerfile
###########################################################
FROM python:3.13-slim


RUN apt-get update && apt-get install -y git && rm -rf /var/lib/apt/lists/*

RUN pip install --no-cache-dir dbt-core dbt-postgres

WORKDIR /usr/app

# Projet dbt embarqué dans l'image
COPY src/dbt/ /usr/app/
RUN dbt deps

# Copy et lance le entrypoint.sh qui cree le profile.yml
COPY docker/dbt/entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

ENTRYPOINT ["/entrypoint.sh"]