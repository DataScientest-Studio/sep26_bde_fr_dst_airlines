FROM jupyter/pyspark-notebook:latest

USER root

RUN apt-get update && \
    apt-get install -y wget && \
    rm -rf /var/lib/apt/lists/*

RUN mkdir -p /opt/spark-extra-jars

# GCS Connector
RUN wget \
    https://storage.googleapis.com/hadoop-lib/gcs/gcs-connector-hadoop3-latest.jar \
    -O /opt/spark-extra-jars/gcs-connector.jar

# PostgreSQL JDBC Driver
RUN wget \
    https://jdbc.postgresql.org/download/postgresql-42.7.8.jar \
    -O /opt/spark-extra-jars/postgresql.jar

# Dépendances Python
RUN pip install --no-cache-dir \
    google-cloud-storage \
    google-cloud-secret-manager \
    psycopg2-binary \
    mlflow \
    xgboost \
    pyarrow \
    requests

USER ${NB_UID}
