FROM python:3.13-slim

ENV PYTHONUNBUFFERED=1
WORKDIR /app

COPY src/airlabs_collect/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY src/airlabs_collect/ .

# Cloud Run fournit le port dans $PORT (8080 par défaut)
CMD exec functions-framework --target=run_http --port=${PORT:-8080}