FROM python:3.13-slim

WORKDIR /app

COPY src/data/airlabs_collect/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY src/data/airlabs_collect/collect_airlabs.py .

ENTRYPOINT ["python", "collect_airlabs.py"]