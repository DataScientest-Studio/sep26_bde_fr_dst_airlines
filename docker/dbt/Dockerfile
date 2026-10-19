###########################################################
# DBT Dockerfile
###########################################################
FROM python:3.13-slim


RUN apt-get update && \
    apt-get install -y git && \
    rm -rf /var/lib/apt/lists/*

RUN pip install --no-cache-dir \
    dbt-core \
    dbt-postgres

WORKDIR /usr/app