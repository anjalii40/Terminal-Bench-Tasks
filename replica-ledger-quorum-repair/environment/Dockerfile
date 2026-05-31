FROM python:3.10.14-slim

WORKDIR /app

RUN apt-get update \
    && apt-get install -y --no-install-recommends bash \
    && rm -rf /var/lib/apt/lists/* \
    && pip install --no-cache-dir pytest==8.3.2

RUN mkdir -p /app/state /app/output

COPY reconcile.py /app/reconcile.py
COPY checkpoint.json /app/checkpoint.json
COPY replica_a.jsonl /app/replica_a.jsonl
COPY replica_b.jsonl /app/replica_b.jsonl
COPY replica_c.jsonl /app/replica_c.jsonl
