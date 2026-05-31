FROM python:3.10.14-slim

WORKDIR /

RUN apt-get update \
    && apt-get install -y --no-install-recommends bash \
    && rm -rf /var/lib/apt/lists/* \
    && pip install --no-cache-dir pytest==8.3.2

COPY bookbinder.py visible_plan.json /environment/
